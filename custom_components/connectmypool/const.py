"""Constants for the ConnectMyPool integration."""

DOMAIN = "connectmypool"

CONF_POOL_API_CODE = "pool_api_code"
CONF_POOL_NAME = "pool_name"

API_BASE_URL = "https://www.connectmypool.com.au/api"
API_POOL_CONFIG = f"{API_BASE_URL}/poolconfig"
API_POOL_STATUS = f"{API_BASE_URL}/poolstatus"
API_POOL_ACTION = f"{API_BASE_URL}/poolaction"
API_POOL_ACTION_STATUS = f"{API_BASE_URL}/poolactionstatus"

DEFAULT_SCAN_INTERVAL = 61  # seconds — just outside the API's 60s throttle window

# Action codes
ACTION_CYCLE_CHANNEL = 1
ACTION_SET_VALVE_MODE = 2
ACTION_SET_POOL_SPA = 3
ACTION_SET_HEATER_MODE = 4
ACTION_SET_HEATER_TEMP = 5
ACTION_SET_LIGHT_MODE = 6
ACTION_SET_LIGHT_COLOR = 7
ACTION_SET_FAVOURITE = 8
ACTION_SET_SOLAR_MODE = 9
ACTION_SET_SOLAR_TEMP = 10
ACTION_LIGHT_SYNC = 11
ACTION_SET_HEAT_COOL = 12

# Enumerations
POOL_SPA_MODES = {0: "Spa", 1: "Pool"}
HEAT_COOL_MODES = {0: "Cooling", 1: "Heating"}
HEATER_MODES = {0: "Off", 1: "On"}
SOLAR_MODES = {0: "Off", 1: "Auto", 2: "On"}
CHANNEL_MODES = {0: "Off", 1: "Auto", 2: "On", 3: "Low Speed", 4: "Medium Speed", 5: "High Speed"}
VALVE_MODES = {0: "Off", 1: "Auto", 2: "On"}
LIGHT_MODES = {0: "Off", 1: "Auto", 2: "On"}

LIGHT_COLORS = {
    1: "Red", 2: "Orange", 3: "Yellow", 4: "Green", 5: "Blue",
    6: "Purple", 7: "White", 8: "User 1", 9: "User 2", 10: "Disco",
    11: "Smooth", 12: "Fade", 13: "Magenta", 14: "Cyan", 15: "Pattern",
    16: "Rainbow", 17: "Ocean", 18: "Voodoo Lounge", 19: "Deep Blue Sea",
    20: "Royal Blue", 21: "Afternoon Skies", 22: "Aqua Green", 23: "Emerald",
    24: "Warm Red", 25: "Flamingo", 26: "Vivid Violet", 27: "Sangria",
    28: "Twilight", 29: "Tranquillity", 30: "Gemstone", 31: "USA",
    32: "Mardi Gras", 33: "Cool Cabaret", 34: "Sam", 35: "Party",
    36: "Romance", 37: "Caribbean", 38: "American", 39: "California Sunset",
    40: "Royal", 41: "Hold", 42: "Recall", 43: "Peruvian Paradise",
    44: "Super Nova", 45: "Northern Lights", 46: "Tidal Wave",
    47: "Patriot Dream", 48: "Desert Skies", 49: "Nova", 50: "Pink",
}

# Channel functions (from API docs)
CHANNEL_FUNCTIONS = {
    1: "Filter Pump", 2: "Cleaning Pump", 3: "Heater Pump",
    4: "Booster Pump", 5: "Waterfall Pump", 6: "Fountain Pump",
    7: "Spa Pump", 8: "Solar Pump", 9: "Blower", 10: "Swimjet",
    11: "Jets", 12: "Spa Jets", 13: "Overflow", 14: "Spillway",
    15: "Audio", 16: "Hot Seat", 17: "Heater Power", 18: "Custom",
}

# Valve functions
VALVE_FUNCTIONS = {1: "Pool/Spa", 2: "Solar"}

PLATFORMS = ["sensor", "switch", "select", "number"]
