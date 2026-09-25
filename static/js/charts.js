/*
 * AI Food Inventory Management System
 * Charts.js Configuration and Utilities
 * Version: 1.0.0
 */

class InventoryCharts {
    constructor() {
        this.colors = {
            primary: '#4361ee',
            secondary: '#f72585',
            success: '#4ade80',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#0ea5e9',
            light: '#f8f9fa',
            dark: '#212529',
            categories: [
                '#4361ee', '#f72585', '#4cc9f0', '#7209b7', 
                '#f8961e', '#43aa8b', '#577590', '#f94144',
                '#90be6d', '#f9c74f', '#277da1', '#4d908e'
            ]
        };
        
        this.charts = new Map();
        this.defaultOptions = this.getDefaultOptions();
    }
    
    getDefaultOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(33, 37, 41, 0.95)',
                    titleFont: {
                        family: "'Poppins', sans-serif",
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        family: "'Poppins', sans-serif",
                        size: 12
                    },
                    padding: 12,
                    cornerRadius: 6,
                    displayColors: true,
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        borderDash: [5, 5],
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 11
                        },
                        padding: 10
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        };
    }
    
    // Initialize Chart.js with custom configurations
    init() {
        // Register custom colors
        Chart.defaults.backgroundColor = this.colors.primary;
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.color = '#6c757d';
        Chart.defaults.font.family = "'Poppins', sans-serif";
        Chart.defaults.font.size = 12;
        
        console.log('Inventory Charts initialized');
    }
    
    // Create inventory by category chart
    createCategoryChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: this.colors.categories,
                    borderColor: '#fff',
                    borderWidth: 2,
                    hoverOffset: 15
                }]
            },
            options: {
                ...this.defaultOptions,
                cutout: '70%',
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'bottom'
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create demand prediction chart
    createDemandChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Predicted Demand',
                    data: data.values || [],
                    borderColor: this.colors.primary,
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return `Predicted: ${context.parsed.y} units`;
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create expiry tracking chart
    createExpiryChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Expiring Items',
                    data: data.values || [],
                    backgroundColor: data.colors || this.generateExpiryColors(data.values || []),
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        title: {
                            display: true,
                            text: 'Number of Items',
                            font: {
                                weight: '600'
                            }
                        }
                    },
                    x: {
                        ...this.defaultOptions.scales.x,
                        title: {
                            display: true,
                            text: 'Days to Expiry',
                            font: {
                                weight: '600'
                            }
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y} items`;
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create sales performance chart
    createSalesChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Sales Revenue',
                    data: data.revenue || [],
                    borderColor: this.colors.success,
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                }, {
                    label: 'Units Sold',
                    data: data.units || [],
                    borderColor: this.colors.info,
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    x: {
                        ...this.defaultOptions.scales.x,
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        ...this.defaultOptions.scales.y,
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Revenue ($)',
                            font: {
                                weight: '600'
                            }
                        },
                        grid: {
                            drawBorder: false
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Units Sold',
                            font: {
                                weight: '600'
                            }
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create waste analysis chart
    createWasteChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: this.generateWasteColors(data.values || []),
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    r: {
                        ticks: {
                            display: false
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create stock level gauge chart
    createStockGauge(canvasId, current, min, max, label) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const percentage = ((current - min) / (max - min)) * 100;
        const color = this.getStockLevelColor(percentage);
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [label],
                datasets: [{
                    data: [percentage, 100 - percentage],
                    backgroundColor: [color, 'rgba(0, 0, 0, 0.05)'],
                    borderWidth: 0,
                    circumference: 270,
                    rotation: 225
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '80%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            },
            plugins: [{
                id: 'gaugeText',
                afterDraw: (chart) => {
                    const { ctx, chartArea: { width, height } } = chart;
                    ctx.save();
                    
                    const text = `${current}/${max}`;
                    const subText = `${Math.round(percentage)}%`;
                    
                    ctx.font = 'bold 24px Poppins';
                    ctx.fillStyle = color;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(text, width / 2, height / 2 - 10);
                    
                    ctx.font = '12px Poppins';
                    ctx.fillStyle = '#6c757d';
                    ctx.fillText(subText, width / 2, height / 2 + 20);
                    
                    ctx.restore();
                }
            }]
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create real-time inventory chart
    createRealTimeChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: data.datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data,
                    borderColor: dataset.color || this.colors.primary,
                    backgroundColor: dataset.color ? this.hexToRgba(dataset.color, 0.1) : 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }))
            },
            options: {
                ...this.defaultOptions,
                animation: {
                    duration: 0
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    streaming: {
                        duration: 20000,
                        refresh: 1000,
                        delay: 2000,
                        onRefresh: (chart) => {
                            // This would be called to update the chart with new data
                            // In a real application, you would fetch new data here
                        }
                    }
                },
                scales: {
                    x: {
                        ...this.defaultOptions.scales.x,
                        type: 'realtime',
                        realtime: {
                            duration: 20000,
                            refresh: 1000,
                            delay: 2000,
                            onRefresh: (chart) => {
                                // Update chart with new data
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create comparison chart (multiple datasets)
    createComparisonChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: data.datasets.map((dataset, index) => ({
                    label: dataset.label,
                    data: dataset.data,
                    backgroundColor: dataset.color || this.colors.categories[index % this.colors.categories.length],
                    borderRadius: 4
                }))
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    x: {
                        ...this.defaultOptions.scales.x,
                        stacked: data.stacked || false
                    },
                    y: {
                        ...this.defaultOptions.scales.y,
                        stacked: data.stacked || false
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create trend analysis chart
    createTrendChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Actual',
                    data: data.actual || [],
                    borderColor: this.colors.primary,
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 0
                }, {
                    label: 'Trend',
                    data: data.trend || [],
                    borderColor: this.colors.success,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 0
                }, {
                    label: 'Prediction',
                    data: data.prediction || [],
                    borderColor: this.colors.info,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [3, 3],
                    tension: 0.4,
                    pointRadius: 0,
                    fill: {
                        target: '-1',
                        above: 'rgba(14, 165, 233, 0.1)'
                    }
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Create heatmap chart for inventory movements
    createHeatmapChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Inventory Movements',
                    data: data.points || [],
                    backgroundColor: (context) => {
                        const value = context.dataset.data[context.dataIndex].v;
                        const alpha = Math.min(Math.max(value / 100, 0.1), 1);
                        return `rgba(67, 97, 238, ${alpha})`;
                    },
                    borderWidth: 1,
                    borderColor: '#fff',
                    width: ({ chart }) => (chart.chartArea.width / 24) - 1,
                    height: ({ chart }) => (chart.chartArea.height / 7) - 1
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    x: {
                        ...this.defaultOptions.scales.x,
                        type: 'time',
                        time: {
                            unit: 'day'
                        },
                        offset: true
                    },
                    y: {
                        ...this.defaultOptions.scales.y,
                        type: 'category',
                        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        offset: true
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            title: (items) => {
                                return items[0].raw.x.toLocaleDateString();
                            },
                            label: (context) => {
                                return `Movements: ${context.raw.v}`;
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Update an existing chart with new data
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (!chart) {
            console.error(`Chart with id ${canvasId} not found`);
            return;
        }
        
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        
        if (newData.datasets) {
            chart.data.datasets = newData.datasets;
        } else if (newData.values) {
            chart.data.datasets[0].data = newData.values;
        }
        
        chart.update();
        return chart;
    }
    
    // Refresh all charts
    refreshAll() {
        this.charts.forEach(chart => {
            chart.update();
        });
    }
    
    // Destroy a chart
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }
    
    // Destroy all charts
    destroyAll() {
        this.charts.forEach(chart => {
            chart.destroy();
        });
        this.charts.clear();
    }
    
    // Generate colors based on expiry days
    generateExpiryColors(values) {
        return values.map(value => {
            if (value <= 1) return this.colors.danger;
            if (value <= 3) return this.colors.warning;
            if (value <= 7) return this.colors.info;
            return this.colors.success;
        });
    }
    
    // Generate colors for waste chart
    generateWasteColors(values) {
        const max = Math.max(...values);
        return values.map(value => {
            const intensity = value / max;
            return `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`;
        });
    }
    
    // Get color based on stock level percentage
    getStockLevelColor(percentage) {
        if (percentage < 20) return this.colors.danger;
        if (percentage < 50) return this.colors.warning;
        if (percentage < 80) return this.colors.info;
        return this.colors.success;
    }
    
    // Convert hex to rgba
    hexToRgba(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    // Generate sample data for demonstration
    generateSampleData(type, count = 10) {
        switch (type) {
            case 'category':
                return {
                    labels: ['Dairy', 'Bakery', 'Beverages', 'Vegetables', 'Fruits', 'Meat', 'Frozen', 'Snacks', 'Canned', 'Condiments'],
                    values: [25, 18, 15, 12, 10, 8, 6, 5, 4, 3]
                };
                
            case 'demand':
                const labels = [];
                const values = [];
                for (let i = 0; i < count; i++) {
                    labels.push(`Day ${i + 1}`);
                    values.push(Math.floor(Math.random() * 100) + 50);
                }
                return { labels, values };
                
            case 'expiry':
                return {
                    labels: ['Expired', 'Today', '1-3 Days', '4-7 Days', '1-2 Weeks', '2+ Weeks'],
                    values: [3, 2, 5, 8, 12, 45],
                    colors: [
                        this.colors.danger,
                        this.colors.danger,
                        this.colors.warning,
                        this.colors.warning,
                        this.colors.info,
                        this.colors.success
                    ]
                };
                
            case 'sales':
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const revenue = months.map(() => Math.floor(Math.random() * 10000) + 5000);
                const units = months.map(() => Math.floor(Math.random() * 500) + 200);
                return { labels: months, revenue, units };
                
            case 'waste':
                return {
                    labels: ['Expired', 'Damaged', 'Overstock', 'Seasonal', 'Returns'],
                    values: [35, 25, 20, 15, 5]
                };
                
            default:
                return { labels: [], values: [] };
        }
    }
    
    // Create animated chart with progress
    createProgressChart(canvasId, current, total, label = 'Progress') {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const percentage = (current / total) * 100;
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [percentage, 100 - percentage],
                    backgroundColor: [this.getStockLevelColor(percentage), 'rgba(0, 0, 0, 0.05)'],
                    borderWidth: 0,
                    borderRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            },
            plugins: [{
                id: 'progressText',
                afterDraw: (chart) => {
                    const { ctx, chartArea: { width, height } } = chart;
                    ctx.save();
                    
                    ctx.font = 'bold 20px Poppins';
                    ctx.fillStyle = this.getStockLevelColor(percentage);
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(`${Math.round(percentage)}%`, width / 2, height / 2);
                    
                    ctx.font = '12px Poppins';
                    ctx.fillStyle = '#6c757d';
                    ctx.fillText(label, width / 2, height / 2 + 25);
                    
                    ctx.restore();
                }
            }]
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    // Export chart as image
    exportChart(canvasId, filename = 'chart') {
        const chart = this.charts.get(canvasId);
        if (!chart) {
            console.error(`Chart with id ${canvasId} not found`);
            return;
        }
        
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = chart.toBase64Image();
        link.click();
    }
    
    // Print chart
    printChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (!chart) {
            console.error(`Chart with id ${canvasId} not found`);
            return;
        }
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print Chart</title>
                    <style>
                        body { margin: 0; padding: 20px; }
                        img { max-width: 100%; height: auto; }
                    </style>
                </head>
                <body>
                    <img src="${chart.toBase64Image()}" />
                    <script>
                        window.onload = function() {
                            window.print();
                            window.onafterprint = function() {
                                window.close();
                            };
                        };
                    </script>
                </body>
            </html>
        `);
        printWindow.document.close();
    }
    
    // Add resize listener for responsive charts
    addResizeListener() {
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                this.refreshAll();
            }, 250);
        });
    }
    
    // Initialize all charts on page
    initPageCharts() {
        document.querySelectorAll('[data-chart-type]').forEach(element => {
            const canvasId = element.id;
            const chartType = element.getAttribute('data-chart-type');
            const dataSource = element.getAttribute('data-source');
            
            if (!canvasId || !chartType) return;
            
            // Generate or fetch data based on data-source attribute
            let data;
            if (dataSource) {
                // In a real application, you would fetch data from the server
                data = this.generateSampleData(dataSource);
            } else {
                data = this.generateSampleData(chartType);
            }
            
            // Create chart based on type
            switch (chartType) {
                case 'category':
                    this.createCategoryChart(canvasId, data);
                    break;
                case 'demand':
                    this.createDemandChart(canvasId, data);
                    break;
                case 'expiry':
                    this.createExpiryChart(canvasId, data);
                    break;
                case 'sales':
                    this.createSalesChart(canvasId, data);
                    break;
                case 'waste':
                    this.createWasteChart(canvasId, data);
                    break;
                case 'trend':
                    this.createTrendChart(canvasId, data);
                    break;
                case 'comparison':
                    this.createComparisonChart(canvasId, data);
                    break;
                default:
                    console.warn(`Unknown chart type: ${chartType}`);
            }
        });
        
        // Add resize listener
        this.addResizeListener();
    }
}

// Create global instance
const inventoryCharts = new InventoryCharts();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    inventoryCharts.init();
    inventoryCharts.initPageCharts();
    
    // Add custom tooltip styles
    const style = document.createElement('style');
    style.textContent = `
        .chart-tooltip {
            background: rgba(33, 37, 41, 0.95) !important;
            border-radius: 6px !important;
            border: none !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
            padding: 12px !important;
        }
        
        .chart-tooltip .tooltip-title {
            font-family: 'Poppins', sans-serif;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
            color: #fff;
        }
        
        .chart-tooltip .tooltip-body {
            font-family: 'Poppins', sans-serif;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.9);
        }
        
        .chartjs-tooltip-key {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 6px;
        }
    `;
    document.head.appendChild(style);
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { InventoryCharts, inventoryCharts };
}