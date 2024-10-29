"use strict";

// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};

app.data = {    
    data: function() {
        return {
            user_checklist_list: [],
            totals: {},
            species: [],
            searchQuery: "",
            selectedSpecies: null,
            speciesDates: []
        };
    },
    computed: {
        filteredTotals: function() {
            let query = this.searchQuery.toLowerCase();
            return Object.fromEntries(
                Object.entries(this.totals).filter(([key, value]) => key.toLowerCase().includes(query))
            );
        }
    },
    methods: {
        selectSpecies: function(species) {
            this.selectedSpecies = species;
            this.speciesDates = this.user_checklist_list
                .filter(checklist => checklist.content[species])
                .map(checklist => ({ date: checklist.created_on, count: checklist.content[species], location: checklist.location }));
            
            this.$nextTick(() => {
                this.visualizeDates();
            });
        },
        visualizeDates: function() {
            // Clear any existing visualization
            d3.select("#visualization").selectAll("*").remove();
        
            // Create a new visualization
            let svg = d3.select("#visualization")
                        .append("svg")
                        .attr("width", 500)
                        .attr("height", 300);
        
            let dates = this.speciesDates.map(d => new Date(d.date));
            let counts = this.speciesDates.map(d => d.count);
        
            let xScale = d3.scaleTime()
                           .domain(d3.extent(dates))
                           .range([50, 450]);
        
            let yScale = d3.scaleLinear()
                           .domain([0, d3.max(counts)])
                           .range([250, 50]);
        
            let xAxis = d3.axisBottom(xScale).ticks(5);
            // Adjust the number of ticks for the y-axis to avoid overcrowding
            let yAxis = d3.axisLeft(yScale).ticks(Math.min(d3.max(counts), 10)).tickFormat(d3.format("d"));
        
            svg.append("g")
               .attr("transform", "translate(0, 250)")
               .call(xAxis);
        
            svg.append("g")
               .attr("transform", "translate(50, 0)")
               .call(yAxis);
        
            svg.append("text")
               .attr("transform", "translate(250, 290)")
               .style("text-anchor", "middle")
               .text("Date Seen");
        
            svg.append("text")
               .attr("transform", "rotate(-90)")
               .attr("y", 15)
               .attr("x", -150)
               .style("text-anchor", "middle")
               .text("Count");
        
            svg.selectAll("circle")
               .data(this.speciesDates)
               .enter()
               .append("circle")
               .attr("cx", d => xScale(new Date(d.date)))
               .attr("cy", d => yScale(d.count))
               .attr("r", 5)
               .append("title")
               .text(d => `Date: ${d.date}, Count: ${d.count}, Location: ${d.location}`);
        }
    }
};

app.vue = Vue.createApp(app.data).mount("#app");

app.load_data = function () {
    axios.get(load_data_url).then(function(r) {
            let totals = {};
            let user_checklist_list = r.data.user_checklist_list;
            for (let checklist of user_checklist_list) {
                for (let species in checklist.content) {
                    if (totals[species]) {
                        totals[species] += checklist.content[species];
                    } else {
                        totals[species] = checklist.content[species];
                    }
                }
            }
            app.vue.user_checklist_list = user_checklist_list;
            app.vue.totals = totals;
    });
}

app.load_data();