@service
def bathroom_motion():
    task.unique("bathroom_motion")
    log.info(f"triggered; turning on the bathroom light on 5 min")
    if switch.bathroom_pointslights != "on":
        switch.turn_on(entity_id="switch.bathroom_pointslights")
        switch.turn_on(entity_id="switch.bathroom_switch_1_green_2")
    task.sleep(300)
    switch.turn_off(entity_id="switch.bathroom_pointslights")
    switch.turn_off(entity_id="switch.bathroom_switch_1_green_2")
