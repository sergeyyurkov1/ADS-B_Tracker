window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {
                const marker_ = L.icon({
                    iconUrl: 'assets/4.png',
                });
                const true_track = feature.properties.true_track;

                return L.marker(latlng, {
                    icon: marker_,
                    rotationAngle: true_track
                });
            }

            ,
        function1: function(feature, latlng, context) {
            const point_count = feature.properties.point_count;
            const size =
                point_count <= 5 ? 'small' :
                point_count > 5 && point_count <= 10 ? 'medium' : 'large';
            const icon = L.divIcon({
                html: `<div><span>${ feature.properties.point_count_abbreviated }</span></div>`,
                className: `marker-cluster marker-cluster-${ size }`,
                iconSize: L.point(40, 40)
            });

            return L.marker(latlng, {
                icon
            });
        }

    }
});