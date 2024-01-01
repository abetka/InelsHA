@state_trigger("security.rear_motion == '1' or security.side_motion == '1'")
@time_active("range(sunset - 20min, sunrise + 20min)")
def motion_light_rear():
    """Turn on rear light for 5 minutes when there is motion and it's dark"""
    task.unique("motion_light_rear")
    log.info(f"triggered; turning on the light")
    if light.outside_rear != "on":
        light.turn_on(entity_id="light.outside_rear", brightness=255)
    task.sleep(300)
    light.turn_off(entity_id="light.outside_rear")