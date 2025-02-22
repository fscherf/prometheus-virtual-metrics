PLUGIN_HOOK_NAMES = [

    # server hooks
    'on_startup',
    'on_shutdown',

    # prometheus API hooks
    'on_instant_query_request',
    'on_range_query_request',
    'on_metric_names_request',
    'on_label_names_request',
    'on_label_values_request',
]
