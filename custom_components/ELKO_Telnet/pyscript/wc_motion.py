@service
def wc_motion():
    task.unique("wc_motion")
    log.info(f"triggered; turning on the wc light on 5 min")
    if switch.wc_pointslights != "on":
        switch.turn_on(entity_id="switch.wc_pointslights")
        switch.turn_on(entity_id="switch.wc_switch_1_green_1")
    task.sleep(300)
    switch.turn_off(entity_id="switch.wc_pointslights")
    switch.turn_off(entity_id="switch.wc_switch_1_green_1")