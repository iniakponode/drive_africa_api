"@HiltWorker
class UploadRawSensorDataWorker @AssistedInject constructor(
        @Assisted appContext: Context,
        @Assisted workerParams: WorkerParameters,
        private val repository: RawSensorDataApiRepository,
        private val locationLocalRepository: LocationRepository,
        private val locationApiRepository: LocationApiRepository,
        private val localRawDataRepository: RawSensorDataRepository,
        private val unsafeBehavioursLocalRepository: UnsafeBehaviourRepository,
        private val unsafeBehavioursApiRepository: UnsafeBehaviourApiRepository,
        private val aiModelInputLocalRepository: AIModelInputRepository,
        private val aiModelInputApiRepository: AIModelInputApiRepository,
        private val reportStatisticsLocalRepository: ReportStatisticsRepository,
        private val reportStatisticsApiRepository: ReportStatisticsApiRepository
    ) : CoroutineWorker(appContext, workerParams) {

        companion object {
            private const val BATCH_SIZE = 500 // Adjust as needed
        }

        override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
            val vehicleNotificationManager = VehicleNotificationManager(applicationContext)

            // Check network connectivity
            val connectivityManager = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val capabilities = connectivityManager.getNetworkCapabilities(connectivityManager.activeNetwork)
            val isConnected = capabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) == true
            if (!isConnected) return@withContext Result.retry()

            suspend fun <T> attemptUploadInBatches(
                notificationTitle: String,
                data: List<T>,
                batchUploadAction: suspend (List<T>) -> Resource<Unit>,
                onSuccessForBatch: suspend (List<T>) -> Unit
            ): Boolean {
                if (data.isEmpty()) return true

                val chunks = data.chunked(BATCH_SIZE)
                for ((index, chunk) in chunks.withIndex()) {
                    vehicleNotificationManager.displayNotification(notificationTitle, "Uploading batch ${index + 1} of ${chunks.size}...")
                    val result = batchUploadAction(chunk)
                    if (result is Resource.Error) {
                        vehicleNotificationManager.displayNotification(notificationTitle, "Failed to upload. Retrying...")
                        return false
                    } else {
                        // Mark batch as synced/processed
                        onSuccessForBatch(chunk)
                    }
                }
                return true
            }

            // Upload Locations
            val unsyncedLocations = locationLocalRepository.getLocationBySynced(false).firstOrNull().orEmpty()
            val locationsList = unsyncedLocations.map {
                LocationCreate(
                    longitude = it.longitude,
                    latitude = it.latitude,
                    timestamp = it.timestamp,
                    date = DateConversionUtils.dateToString(it.date) ?: "",
                    altitude = it.altitude,
                    speed = it.speed.toDouble(),
                    distance = it.distance.toDouble(),
                    sync = true
                )
            }
            if (!attemptUploadInBatches(
                    notificationTitle = "Data Upload: Locations",
                    data = locationsList,
                    batchUploadAction = { locationApiRepository.batchCreateLocations(it) },
                    onSuccessForBatch = { batch ->
                        val updated = batch.mapNotNull { locCreate ->
                            unsyncedLocations.find { original ->
                                original.longitude == locCreate.longitude &&
                                        original.latitude == locCreate.latitude &&
                                        original.timestamp == locCreate.timestamp
                            }?.copy(sync = true)
                        }
                        updated.forEach { locationLocalRepository.updateLocation(it) }
                    }
                )
            ) return@withContext Result.retry()

            // Upload Unsafe Behaviours
            val unsyncedUnsafeBehaviours = unsafeBehavioursLocalRepository.getUnsafeBehavioursBySyncStatus(false)
            val unsyncedUnsafeBehavioursList = unsyncedUnsafeBehaviours.map {
                UnsafeBehaviourCreate(
                    id=it.id,
                    trip_id = it.tripId,
                    location_id = it.locationId!!,
                    driverProfileId = it.driverProfileId,
                    behaviour_type = it.behaviorType,
                    severity = it.severity.toDouble(),
                    timestamp = it.timestamp,
                    date = DateConversionUtils.dateToString(it.date) ?: ""
                )
            }
            if (!attemptUploadInBatches(
                    notificationTitle = "Data Upload: Unsafe Behaviours",
                    data = unsyncedUnsafeBehavioursList,
                    batchUploadAction = { unsafeBehavioursApiRepository.batchCreateUnsafeBehaviours(it) },
                    onSuccessForBatch = { batch ->
                        val updated = batch.mapNotNull { ubCreate ->
                            unsyncedUnsafeBehaviours.find { original ->
                                original.tripId == ubCreate.trip_id &&
                                        original.locationId== ubCreate.location_id &&
                                        original.driverProfileId== ubCreate.driverProfileId &&
                                        original.timestamp == ubCreate.timestamp
                            }?.copy(synced = true)
                        }
                        updated.forEach { unsafeBehavioursLocalRepository.updateUnsafeBehaviour(it.toDomainModel()) }
                    }
                )
            ) return@withContext Result.retry()

            // Upload Raw Sensor Data
            val localRawSensorData = localRawDataRepository.getSensorDataBySyncStatus(false)
            val driverProfileId = PreferenceUtils.getDriverProfileId(applicationContext)?: return@withContext Result.retry()
            val rawSensorDataList = localRawSensorData.map {
                RawSensorDataCreate(
                    id=it.id,
                    sensor_type = it.sensorType,
                    sensor_type_name = it.sensorTypeName,
                    values = it.values,
                    timestamp = it.timestamp,
                    date = DateConversionUtils.dateToString(it.date),
                    accuracy = it.accuracy,
                    location_id = it.locationId,
                    trip_id = it.tripId!!,
                    driverProfileId = driverProfileId,
                    sync = true
                )
            }
            if (!attemptUploadInBatches(
                    notificationTitle = "Data Upload: Sensor Data",
                    data = rawSensorDataList,
                    batchUploadAction = { repository.batchCreateRawSensorData(it) },
                    onSuccessForBatch = { batch ->
                        // Mark as synced and delete locally if needed
                        val updatedData = batch.mapNotNull { rsCreate ->
                            localRawSensorData.find { original ->
                                original.locationId== rsCreate.location_id &&
                                        original.tripId== rsCreate.trip_id &&
                                        original.timestamp == rsCreate.timestamp
                            }?.copy(sync = true)
                        }
                        updatedData.forEach { localRawDataRepository.updateRawSensorData(it.toEntity()) }
                        localRawDataRepository.deleteRawSensorDataByIds(updatedData.map { d -> d.id })
                    }
                )
            ) return@withContext Result.retry()

            // Upload AI Model Inputs
            val unsyncedAIModelInputs = aiModelInputLocalRepository.getAiModelInputsBySyncStatus(false)
            val unsyncedAIModelInputsList = unsyncedAIModelInputs.map { input ->
                AIModelInputCreate(
                    id=input.id,
                    trip_id = input.tripId,
                    driver_profile_id = input.driverProfileId,
                    timestamp = DateConversionUtils.longToTimestampString(input.timestamp),
                    startTimeStamp = DateConversionUtils.longToTimestampString(input.startTimestamp),
                    endTimeStamp = DateConversionUtils.longToTimestampString(input.endTimestamp),
                    date = DateConversionUtils.dateToString(input.date) ?: "",
                    hour_of_day_mean = input.hourOfDayMean,
                    day_of_week_mean = input.dayOfWeekMean.toDouble(),
                    speed_std = input.speedStd.toDouble(),
                    course_std = input.courseStd.toDouble(),
                    acceleration_y_original_mean = input.accelerationYOriginalMean.toDouble(),
                    synced = true
                )
            }
            if (!attemptUploadInBatches(
                    notificationTitle = "Data Upload: AI Model Inputs",
                    data = unsyncedAIModelInputsList,
                    batchUploadAction = { aiModelInputApiRepository.batchCreateAiModelInputs(it) },
                    onSuccessForBatch = { batch ->
                        val updated = batch.mapNotNull { aiCreate ->
                            unsyncedAIModelInputs.find { original ->
                                original.tripId == aiCreate.trip_id &&
                                        original.driverProfileId == aiCreate.driver_profile_id &&
                                        original.timestamp == DateConversionUtils.timestampStringToLong(aiCreate.timestamp)
                            }?.copy(sync = true)
                        }
                        updated.forEach { aiModelInputLocalRepository.updateAiModelInput(it) }
                    }
                )
            ) return@withContext Result.retry()

            // Upload Report Statistics
            val unsyncedReportStatistics = reportStatisticsLocalRepository.getReportStatisticsBySyncStatus(false)
            val reportStatisticsList = unsyncedReportStatistics.map { it.toReportStatisticsCreate() }
            if (!attemptUploadInBatches(
                    notificationTitle = "Data Upload: Report Statistics",
                    data = reportStatisticsList,
                    batchUploadAction = { reportStatisticsApiRepository.batchCreateReportStatistics(it) },
                    onSuccessForBatch = { batch ->
                        val updated = batch.mapNotNull { rsCreate ->
                            unsyncedReportStatistics.find { original -> original.id == rsCreate.id }?.copy(sync = true)
                        }
                        updated.forEach { reportStatisticsLocalRepository.updateReportStatistics(it.toDomainModel()) }
                    }
                )
            ) return@withContext Result.retry()

            // If we reached here, all uploads succeeded
            Result.success()
        }
    }". 