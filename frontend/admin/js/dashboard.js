// Global chart instances for cleanup
let earningsChart, statusChart, visitorsChart, ordersChart;

async function loadStats(){
    const now = Date.now();
    if(statsCache && (now - statsCache.timestamp) < cacheExpiry){
        const stats = statsCache.data;
        updateStatsDisplay(stats);
        renderCharts(stats);
        return;
    }

    try{
        const stats = await apiCall('/admin/api/stats');
        if(!stats.error){
            statsCache = { data: stats, timestamp: now };
            updateStatsDisplay(stats);
            renderCharts(stats);
        }
    }catch(e){
        console.error('Error loading stats:', e);
    }
}

function updateStatsDisplay(stats) {
    document.getElementById('statOrders').textContent = stats.total_orders || 0;
    document.getElementById('statDishes').textContent = stats.active_dishes || 0;
    document.getElementById('statRevenue').textContent = '₹' + (stats.revenue || 0).toLocaleString();
    document.getElementById('statPending').textContent = stats.pending_orders || 0;
    document.getElementById('statActiveUsers').textContent = stats.active_users || 0;
    document.getElementById('statVisitors').textContent = stats.daily_visitors?.reduce((sum, day) => sum + day.visitors, 0) || 0;
}

function renderCharts(stats) {
    // Destroy existing charts to prevent memory leaks
    if (earningsChart) earningsChart.destroy();
    if (statusChart) statusChart.destroy();
    if (visitorsChart) visitorsChart.destroy();
    if (ordersChart) ordersChart.destroy();

    renderEarningsChart(stats.monthly_earnings || []);
    renderStatusChart(stats.order_status_stats || []);
    renderVisitorsChart(stats.daily_visitors || []);
    renderOrdersChart(stats.monthly_earnings || []);
}

function renderEarningsChart(monthlyData) {
    const ctx = document.getElementById('earningsChart');
    if (!ctx) return;

    const labels = monthlyData.map(item => item.month);
    const data = monthlyData.map(item => item.earnings);

    earningsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Earnings (₹)',
                data: data,
                backgroundColor: 'rgba(234, 88, 12, 0.8)',
                borderColor: '#EA580C',
                borderWidth: 2,
                borderRadius: 4,
                borderSkipped: false,
                hoverBackgroundColor: '#DC2626',
                hoverBorderColor: '#B91C1C',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '₹' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function renderStatusChart(statusData) {
    const ctx = document.getElementById('statusChart');
    if (!ctx) return;

    const labels = statusData.map(item => item.status.charAt(0).toUpperCase() + item.status.slice(1));
    const data = statusData.map(item => item.count);

    // Color mapping for different statuses
    const colorMap = {
        'completed': '#10B981',
        'pending': '#F59E0B',
        'confirmed': '#3B82F6',
        'cancelled': '#EF4444',
        'unknown': '#6B7280'
    };

    const backgroundColors = labels.map(label =>
        colorMap[label.toLowerCase()] || '#6B7280'
    );

    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#fff',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

function renderVisitorsChart(visitorsData) {
    const ctx = document.getElementById('visitorsChart');
    if (!ctx) return;

    const labels = visitorsData.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    const data = visitorsData.map(item => item.visitors);

    visitorsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Visitors',
                data: data,
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: '#3B82F6',
                borderWidth: 1,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 10
                    }
                }
            }
        }
    });
}

function renderOrdersChart(monthlyData) {
    const ctx = document.getElementById('ordersChart');
    if (!ctx) return;

    // For order trends, we'll simulate order counts based on earnings
    // In a real app, you'd have separate order count data
    const labels = monthlyData.map(item => item.month);
    const data = monthlyData.map(item => Math.floor(item.earnings / 500)); // Rough estimate

    ordersChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Order Volume',
                data: data,
                borderColor: '#8B5CF6',
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#8B5CF6',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
