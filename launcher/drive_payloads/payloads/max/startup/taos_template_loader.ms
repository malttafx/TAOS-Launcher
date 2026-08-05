-- TAOS Template Loader v1.0
-- Loads the TAOS default scene (ACES/V-Ray template) on 3ds Max startup.
-- Runs ONLY in sessions launched by the TAOS Launcher (this folder is injected
-- via ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR). AYON / vanilla launches never see it.
--
-- Behavior:
--   * Copies the master taos_default.max from the TAOS drive to a local temp
--     cache and loads the CACHED copy - Ctrl+S can never touch the master.
--   * Skips: network render workers, quiet/batch sessions, non-empty scenes.
--   * Warn-never-block: if the drive or file is missing, logs and moves on.
-- Log: %TEMP%\taos_template_loader.log
(
    local logPath = (getDir #temp) + "\\taos_template_loader.log"

    fn tlog msg = (
        try (
            -- MAXScript openFile cannot create a missing file, even in append mode
            if not (doesFileExist logPath) do (
                local c = createFile logPath
                if c != undefined do close c
            )
            local f = openFile logPath mode:"a"
            if f != undefined do (
                format "[%] %\n" localTime msg to:f
                close f
            )
        ) catch ()
        format "TAOS template loader: %\n" msg
    )

    try (
        local proceed = true

        -- Guard 1: never on a render node / batch / quiet session
        if proceed and (IsNetServer()) do (
            tlog "skip - network render server session"
            proceed = false
        )
        if proceed and (GetQuietMode()) do (
            tlog "skip - quiet/batch mode"
            proceed = false
        )

        -- Guard 2: only into a virgin scene (untitled and empty)
        if proceed and (maxFileName != "" or objects.count > 0) do (
            tlog ("skip - scene not empty (file: '" + maxFileName + "', objects: " + (objects.count as string) + ")")
            proceed = false
        )

        if proceed do (
            -- Resolve the TAOS drive (same convention as the menu builder)
            local taosDrive = systemTools.getEnvVariable "TAOSDRIVE"
            if taosDrive == undefined or taosDrive == "" do (
                taosDrive = @"Q:\Shared drives\TAOS"
                tlog "TAOSDRIVE not set - falling back to Q:\\Shared drives\\TAOS"
            )
            -- strip trailing backslash if present
            if taosDrive[taosDrive.count] == "\\" do
                taosDrive = substring taosDrive 1 (taosDrive.count - 1)

            local masterPath = taosDrive + @"\pipeline\launcher\payloads\max\startup_scene\taos_default.max"

            if not (doesFileExist masterPath) then (
                tlog ("WARN - template not found: " + masterPath + " (drive offline?) - starting with empty scene")
            )
            else (
                -- Copy master -> local temp cache; load the cache, never the master.
                local cacheDir = (getDir #temp) + "\\taos_template"
                makeDir cacheDir all:true
                local cachePath = cacheDir + "\\taos_default.max"

                if doesFileExist cachePath do (try (deleteFile cachePath) catch ())
                local copied = false
                try (copied = copyFile masterPath cachePath) catch (copied = false)

                if not copied then (
                    tlog ("WARN - could not copy template to local cache: " + cachePath)
                )
                else (
                    local loaded = false
                    try (loaded = loadMaxFile cachePath useFileUnits:true quiet:true) catch (loaded = false)
                    if loaded then (
                        tlog ("OK - template loaded from cache (" + cachePath + "), master untouched: " + masterPath)
                    )
                    else (
                        tlog ("WARN - loadMaxFile failed for " + cachePath)
                    )
                )
            )
        )
    ) catch (
        tlog ("ERROR - unexpected: " + (getCurrentException()))
    )
)
