-- TAOS 3ds Max payload — v1: confirm the TAOS environment loaded.
-- Runs via ADSK_3DSMAX_STARTUPSCRIPTS_ADDON_DIR set by the TAOS Launcher.
-- Future Max tools (TAOS menu, camera tools, render setup) get added here.
(
    local taosDrive = systemTools.getEnvVariable "TAOSDRIVE"
    if taosDrive == undefined then taosDrive = "<not set>"
    format "TAOS env loaded · TAOSDRIVE = %\n" taosDrive
)
