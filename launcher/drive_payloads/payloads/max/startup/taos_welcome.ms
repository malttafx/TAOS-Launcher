-- TAOS Welcome Card shim v1.0
-- Runs via ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR (TAOS Launcher sessions only).
-- Hands off to pipeline\scripts\3dsmax\startup\taos_welcome_card.py on the drive.
-- Warn-never-block: any failure is silent (logged by the py to %TEMP%\taos_welcome.log).
(
    try (
        local proceed = true
        if (IsNetServer()) do proceed = false
        if proceed and (GetQuietMode()) do proceed = false

        if proceed do (
            local taosDrive = systemTools.getEnvVariable "TAOSDRIVE"
            if taosDrive == undefined or taosDrive == "" do
                taosDrive = @"Q:\Shared drives\TAOS"
            if taosDrive[taosDrive.count] == "\\" do
                taosDrive = substring taosDrive 1 (taosDrive.count - 1)

            local enginePath = taosDrive + @"\pipeline\scripts\3dsmax\startup\taos_welcome_card.py"
            if (doesFileExist enginePath) do (
                python.ExecuteFile enginePath
            )
        )
    ) catch (
        format "TAOS welcome shim: skipped (%)\n" (getCurrentException())
    )
)
