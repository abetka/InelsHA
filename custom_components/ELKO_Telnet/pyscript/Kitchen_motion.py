@service
def kitchen_motion():
    task.unique("kitchen_motion")
    log.info(f"triggered; turning on the kitchen wall light on 5 min")
    if switch.kitchen_backlight_wall != "on":
        switch.turn_on(entity_id="switch.kitchen_backlight_wall")
        switch.turn_on(entity_id="switch.kitchen_switch_1_red_2")
    task.sleep(300)
    switch.turn_off(entity_id="switch.kitchen_backlight_wall")
    switch.turn_off(entity_id="switch.kitchen_switch_1_red_2")
