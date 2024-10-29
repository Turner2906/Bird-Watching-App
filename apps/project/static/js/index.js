"use strict";

// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};

app.data = {
    data: function() {
        return {
            my_value: 1, // Example data
            map: null,
            drawnItems: null,
            shape: null, // Object to store information about the drawn shape
            heatmap: null, // Heatmap layer
            heatData: [], // Array to store heatmap data points
            searchQuery: '',
            speciesList: [],
            filteredSpecies: [],
        };
    },
    methods: {
        my_function: function() {
            this.my_value += 1;
        },
        clearDrawnItems: function() {
            if (this.drawnItems) {
                this.drawnItems.clearLayers(); // Clear existing drawn items
            }
            this.shape = null; // Clear shape information
        },
        initMap: function() { // Initializes the map and heat map!!!
            var map = L.map('map').setView([38.5, -98.0], 5);
            L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
            
            // FeatureGroup is to store editable layers
            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);
            this.drawnItems = drawnItems; // Save to Vue instance

            var drawControl = new L.Control.Draw({
                draw: {
                    polygon: false,
                    marker: false,
                    circle: false,
                    circlemarker: false,
                    polyline: false,
                    rectangle: true
                },
                edit: {
                    featureGroup: drawnItems,
                    edit: false,
                    remove: false 
                }
            });
            map.addControl(drawControl);

            var heatmap = L.heatLayer([], {
                radius: 15,  
                max: 1.0,  
                minOpacity: 0.5, 
                gradient: {1.0: 'blue', 1.0: 'lime', 1.0: 'yellow', 1: 'red'}

            }).addTo(map);
            this.heatmap = heatmap; 

            map.on('draw:created', (event) => {
                this.clearDrawnItems(); // Clear existing drawn items
                var layer = event.layer;
                drawnItems.addLayer(layer); 
                
                // Save shape information
                var shapeData = {
                    type: event.layerType,
                    latlngs: layer.getLatLngs()
                };
                this.shape = shapeData;
            });

            this.map = map; 

            this.addSampleHeatData();
        },
        addSampleHeatData: function() {
            if (!this.searchQuery) {
                axios.get(get_all_species_coordinates_url)
                    .then(response => {
                        if (response.data.error) {
                            console.error('Error:', response.data.error);
                        } else {
                            const coordinates = response.data.coordinates;
                            this.updateHeatmap(coordinates);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching all species coordinates:', error);
                    });
            }
        },
        clearSearch: function() {
            this.searchQuery = '';
            this.addSampleHeatData(); // Reset the heatmap to show all coordinates
        },
        sendShapeDataAndRedirectLocation() { //redirect for location
            if (!this.shape) {
                alert("Select a region on the map");
                return;
            }
            const queryParams = [];
        
            for (let i = 0; i < this.shape.latlngs.length; i++) {
                const coordinateArray = this.shape.latlngs[i];
                coordinateArray.forEach((coord, index) => {
                    const { lat, lng } = coord;
                    const coordinateObject = { lat, lng };
                    queryParams.push(`${index}=${JSON.stringify(coordinateObject)}`);
                });
            }

            const queryString = queryParams.join('&');
        
            const url = `/project/location?${queryString}`;

            window.location.href = url;
        },
        sendShapeDataAndRedirectChecklist() { //redirect for checklist
            if (!this.shape) {
                alert("Select a region on the map");
                return;
            }
            const queryParams = [];
        
            for (let i = 0; i < this.shape.latlngs.length; i++) {
                const coordinateArray = this.shape.latlngs[i];
                coordinateArray.forEach((coord, index) => {
                    const { lat, lng } = coord;
                    const coordinateObject = { lat, lng };
                    queryParams.push(`${index}=${JSON.stringify(coordinateObject)}`);
                });
            }

            const queryString = queryParams.join('&');
        
            const url = `/project/checklist/new?${queryString}`;

            window.location.href = url;
        },
        sendShapeDataAndRedirectStats() {
            // if (!this.shape) {
            //     alert("Select a region on the map");
            //     return;
            // }
            // const queryParams = [];
        
            // for (let i = 0; i < this.shape.latlngs.length; i++) {
            //     const coordinateArray = this.shape.latlngs[i];
            //     coordinateArray.forEach((coord, index) => {
            //         const { lat, lng } = coord;
            //         const coordinateObject = { lat, lng };
            //         queryParams.push(`${index}=${JSON.stringify(coordinateObject)}`);
            //     });
            // }

            // const queryString = queryParams.join('&');
        
            const url = `/project/stats`;

            window.location.href = url;
        },
        fetchSpecies() {
            axios.get(get_species_url)
              .then(response => {
                this.speciesList = response.data.species;
              })
              .catch(error => {
                console.error('Error fetching species:', error);
              });
        },
        filterSpecies() { //searchbar filter
            const query = this.searchQuery.toLowerCase();
            this.filteredSpecies = this.speciesList.filter(species => species.name.toLowerCase().includes(query));
        },
        selectSpecies(species) { //searchbar selection
            this.searchQuery = species.name;
            this.filteredSpecies = [];
            
            // Call the fetchSpeciesCoordinates method to fetch coordinates
            this.fetchSpeciesCoordinates(species.name);
        },
        fetchSpeciesCoordinates(speciesName) { //gets the coordinate for a specific species for heatmap
            axios.get(get_species_coordinates_url, {
                params: {
                    species_name: speciesName
                }
            })
            .then(response => {
                if (response.data.error) {
                    console.error('Error:', response.data.error);
                } else {
                    const coordinates = response.data.coordinates;
                    this.updateHeatmap(coordinates); // Call a function to update the heatmap
                }
            })
            .catch(error => {
                console.error('Error fetching species coordinates:', error);
            });
        },
        updateHeatmap(coordinates) { //updates the heatmap.
            this.heatmap.setLatLngs([]);
        
            coordinates.forEach(coord => {
                this.heatmap.addLatLng([parseFloat(coord.latitude), parseFloat(coord.longitude)]);
            });
        },
    },
    mounted: function() {
        // Initialize the map when the component is mounted
        this.initMap();
        this.fetchSpecies();
    }
};

app.vue = Vue.createApp(app.data).mount("#app");

app.load_data = function () {
    axios.get(my_callback_url).then(function (r) {
        app.vue.my_value = r.data.my_value;
    });
}

app.load_data();
