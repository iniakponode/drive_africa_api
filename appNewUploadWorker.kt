@HiltWorker
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
        private const val BATCH_SIZE = 500
    }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val TAG="uploadWorker"
        Log.d(TAG, "Worker started")  // Log when the worker starts

        if (!checkInternetConnectivity()) {
            Log.e(TAG, "No internet connection. Retrying...")
            return@withContext Result.retry()
        }

        val notificationManager = VehicleNotificationManager(applicationContext)

        if (!uploadLocationData(notificationManager)) {
            Log.e(TAG, "Location data upload failed.")
            return@withContext Result.retry()
        }

        if (!uploadUnsafeBehaviours(notificationManager)) {
            Log.e(TAG, "Unsafe behaviours upload failed.")
            return@withContext Result.retry()
        }

        if (!uploadRawSensorData(notificationManager)) {
            Log.e(TAG, "Raw sensor data upload failed.")
            return@withContext Result.retry()
        }

        if (!uploadAIModelInputs(notificationManager)) {
            Log.e(TAG, "AI model inputs upload failed.")
            return@withContext Result.retry()
        }

        if (!uploadReportStatistics(notificationManager)) {
            Log.e(TAG, "Report statistics upload failed.")
            return@withContext Result.retry()
        }

        cleanupLocalData()
        Log.d(TAG, "Worker completed successfully")  // Log when the worker finishes
        Result.success()
    }

    private fun checkInternetConnectivity(): Boolean {
        val manager = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val capabilities = manager.getNetworkCapabilities(manager.activeNetwork)
        return capabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) == true
    }

    private suspend fun uploadLocationData(notificationManager: VehicleNotificationManager): Boolean {
        val unsyncedLocations = locationLocalRepository
            .getLocationBySynced(false)
            .firstOrNull()
            .orEmpty()

        return uploadInBatches(
            notificationManager,
            notificationTitle = "Data Upload: Locations",
            data = unsyncedLocations,
            timestampSelector = { it.timestamp }, // Long timestamp in Locations
            batchUploadAction = { batch ->
                val payload = batch.map {
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
                locationApiRepository.batchCreateLocations(payload)
            },
            onBatchSuccess = { batch ->
                val synced = batch.map { it.copy(sync = true) }
                synced.forEach { locationLocalRepository.updateLocation(it) }
            }
        )
    }

    private suspend fun uploadUnsafeBehaviours(notificationManager: VehicleNotificationManager): Boolean {
        val unsyncedUnsafeBehaviours = unsafeBehavioursLocalRepository.getUnsafeBehavioursBySyncStatus(false)
        return uploadInBatches(
            notificationManager,
            notificationTitle = "Data Upload: Unsafe Behaviours",
            data = unsyncedUnsafeBehaviours,
            timestampSelector = { it.timestamp }, // Long timestamp in UnsafeBehaviours
            batchUploadAction = { batch ->
                val payload = batch.map {
                    UnsafeBehaviourCreate(
                        id = it.id,
                        trip_id = it.tripId,
                        location_id = it.locationId,
                        driverProfileId = it.driverProfileId,
                        behaviour_type = it.behaviorType,
                        severity = it.severity.toDouble(),
                        timestamp = it.timestamp,
                        date = DateConversionUtils.dateToString(it.date) ?: ""
                    )
                }
                unsafeBehavioursApiRepository.batchCreateUnsafeBehaviours(payload)
            },
            onBatchSuccess = { batch ->
                val synced = batch.map { it.copy(synced = true) }
                synced.forEach {
                    unsafeBehavioursLocalRepository.updateUnsafeBehaviour(it.toDomainModel())
                }
            }
        )
    }

    private suspend fun uploadRawSensorData(notificationManager: VehicleNotificationManager): Boolean {
        val unsyncedSensorData = localRawDataRepository.getSensorDataBySyncStatus(false)
        val driverProfileId = PreferenceUtils.getDriverProfileId(applicationContext) ?: return false

        return uploadInBatches(
            notificationManager,
            notificationTitle = "Data Upload: Sensor Data",
            data = unsyncedSensorData,
            timestampSelector = { it.timestamp }, // Long timestamp in RawSensorData
            batchUploadAction = { batch ->
                val payload = batch.map {
                    RawSensorDataCreate(
                        id = it.id,
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
                repository.batchCreateRawSensorData(payload)
            },
            onBatchSuccess = { batch ->
                val synced = batch.map { it.copy(sync = true) }
                synced.forEach { localRawDataRepository.updateRawSensorData(it.toEntity()) }
            }
        )
    }

    private suspend fun uploadAIModelInputs(notificationManager: VehicleNotificationManager): Boolean {
        val unsyncedAIModelInputs = aiModelInputLocalRepository.getAiModelInputsBySyncStatus(false)
        return uploadInBatches(
            notificationManager,
            notificationTitle = "Data Upload: AI Model Inputs",
            data = unsyncedAIModelInputs,
            timestampSelector = { it.timestamp }, // Long timestamp in AIModelInputs
            batchUploadAction = { batch ->
                val payload = batch.map { input ->
                    AIModelInputCreate(
                        id = input.id,
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
                aiModelInputApiRepository.batchCreateAiModelInputs(payload)
            },
            onBatchSuccess = { batch ->
                val synced = batch.map { it.copy(sync = true) }
                synced.forEach { aiModelInputLocalRepository.updateAiModelInput(it) }
            }
        )
    }

    /**
     * No "timestamp" in ReportStatistics, so let's pick one for ordering.
     * We'll use lastTripStartTime as the sorting key. If it's null, default to 0.
     */
    private suspend fun uploadReportStatistics(notificationManager: VehicleNotificationManager): Boolean {
        val unsyncedStats = reportStatisticsLocalRepository.getReportStatisticsBySyncStatus(false)
        return uploadInBatches(
            notificationManager,
            notificationTitle = "Data Upload: Report Statistics",
            data = unsyncedStats,
            timestampSelector = { stat ->
                stat.lastTripStartTime?.atZone(ZoneId.systemDefault())?.toInstant()?.toEpochMilli() ?: 0
            },
            batchUploadAction = { batch ->
                val payload = batch.map { it.toReportStatisticsCreate() }
                reportStatisticsApiRepository.batchCreateReportStatistics(payload)
            },
            onBatchSuccess = { batch ->
                val synced = batch.map { it.copy(sync = true) }
                synced.forEach { reportStatisticsLocalRepository.updateReportStatistics(it.toDomainModel()) }
            }
        )
    }

    /**
     * Clean up only after everything is synced, checking foreign key references.
     * You need to define the repository/DAO functions below to filter by locationId and sync status.
     */
    private suspend fun cleanupLocalData() {
        // Remove fully synced and unreferenced unsafe behaviours
        val syncedUnsafeBehaviours = unsafeBehavioursLocalRepository.getUnsafeBehaviourBySyncAndProcessedStatus(true,true)
        unsafeBehavioursLocalRepository.deleteUnsafeBehavioursByIds(syncedUnsafeBehaviours.map { it.id })

        // Remove fully synced raw sensor data
        val syncedSensorData = localRawDataRepository.getRawSensorDataBySyncAndProcessedStatus(true,true)
        localRawDataRepository.deleteRawSensorDataByIds(syncedSensorData.map { it.id })

        // Remove fully synced AI model inputs
        val syncedAIInputs = aiModelInputLocalRepository.getAiModelInputsBySyncAndProcessedStatus(true,true)
        aiModelInputLocalRepository.deleteAIModelInputsByIds(syncedAIInputs.map { it.id })

        // Remove fully synced report statistics
        val syncedReportStats = reportStatisticsLocalRepository.getReportStatisticsBySyncAndProcessedStatus(true,true)
        reportStatisticsLocalRepository.deleteReportStatisticsByIds(syncedReportStats.map { it.id })

        // For locations, only delete if not referenced by any unsynced record:
        val syncedLocations = locationLocalRepository
            .getLocationBySynced(true)
            .firstOrNull()
            .orEmpty()

        val deletableLocations = syncedLocations.filter { loc ->
            val stillReferencedByBehaviours = unsafeBehavioursLocalRepository
                .getUnsafeBehavioursByLocationIdAndSyncStatus(loc.id, false, false)
                .isNotEmpty()
            val stillReferencedByRawData = localRawDataRepository
                .getSensorDataByLocationIdAndSyncStatus(loc.id, false, false)
                .isNotEmpty()
            !(stillReferencedByBehaviours || stillReferencedByRawData)
        }

        locationLocalRepository.deleteLocationsByIds(deletableLocations.map { it.id })
    }

    /**
     * Generic batch upload function that:
     * - sorts items by timestampSelector
     * - uploads them in chunks
     * - calls onBatchSuccess if each chunk is uploaded
     * - returns false if any chunk fails
     */
    private suspend fun <T> uploadInBatches(
        notificationManager: VehicleNotificationManager,
        notificationTitle: String,
        data: List<T>,
        timestampSelector: (T) -> Long,
        batchUploadAction: suspend (List<T>) -> Resource<Unit>,
        onBatchSuccess: suspend (List<T>) -> Unit
    ): Boolean {
        if (data.isEmpty()) return true

        val sortedData = data.sortedBy { timestampSelector(it) }
        val chunks = sortedData.chunked(BATCH_SIZE)

        for ((index, chunk) in chunks.withIndex()) {
            notificationManager.displayNotification(
                notificationTitle,
                "Uploading batch ${index + 1} of ${chunks.size}..."
            )
            when (val result = batchUploadAction(chunk)) {
                is Resource.Error -> {
                    notificationManager.displayNotification(
                        notificationTitle,
                        "Failed to upload. Retrying..."
                    )
                    return false
                }
                else -> {
                    onBatchSuccess(chunk)
                }
            }
        }
        return true
    }

}