
# TEMP FILE


europe_west1_overrides = {
    "microsvc-online": {
        "hypesale_autoscale_settings": {
            "minNumReplicas": 1,
            "maxNumReplicas": 250,
            "coolDownPeriodSec": 60,
            "cpuUtilization": {
                "utilizationTarget": 0.7
            }
        },
        "hypesale_create_autoscale": True,
        "hypesale_delete_autoscale": True,
        "hypesale_up_scale_target": 2,
        "hypesale_up_scale_batch_size": 2,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 3,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-mobile": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 3,
        "hypesale_down_scale_target": 1,
    }
}

asia_south1_overrides = {
    "microsvc-online-manual": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 3,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-manual": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 3,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-mobile-manual": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 3,
        "hypesale_down_scale_target": 1,
    }
}

asia_northeast1_overrides = {
    "microsvc-online-manual": {
        "hypesale_up_scale_target": 4,
        "hypesale_up_scale_batch_size": 1,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-manual": {
        "hypesale_up_scale_target": 4,
        "hypesale_up_scale_batch_size": 1,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-mobile-manual": {
        "hypesale_up_scale_target": 4,
        "hypesale_up_scale_batch_size": 1,
        "hypesale_down_scale_target": 1,
    }
}

us_west1_overrides = {
    "microsvc-online-manual": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 2,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-manual": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 2,
        "hypesale_down_scale_target": 1,
    },
    "microsvc-browser-mobile-manual": {
        "hypesale_up_scale_target": 5,
        "hypesale_up_scale_batch_size": 2,
        "hypesale_down_scale_target": 1,
    }
}