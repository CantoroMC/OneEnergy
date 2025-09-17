# OneEnergy - Energy Management System

## Project Overview

**Purpose**: Comprehensive energy management system for analyzing electricity consumption and costs using Italian market data.

**Repository Usage**:

- Energy price database from GME (Gestore Mercati Energetici)
- Consumption data analysis with 15-minute intervals
- Cost optimization through price correlation analysis
- Power BI dashboard development for energy management insights

**Key Features**:

- Real-time energy price tracking (PUN - Prezzo Unico Nazionale)
- DST-aware time series analysis
- Consumption vs. pricing correlation
- Cost forecasting and optimization recommendations

## Development Focus

**DAX Dashboard Components**:

- Energy consumption monitoring with 15-minute granularity
- Cost analysis with real-time pricing integration
- Trend analysis and forecasting models
- Peak usage identification and optimization
- Monthly/yearly cost comparisons
- Energy efficiency KPIs and recommendations

## Performance Optimization Tasks

### CalendarTime Query Optimization

- **Status**: Partially completed - hardcoded years implemented
- **Issue**: Originally used `PUN[DateTime]` causing circular dependency and slow loading
- **Solution**: Temporary hardcoded year range (minY/cY) significantly improved performance
- **Next Steps**:
  - Consider parameterizing year range instead of hardcoding
  - Evaluate if dynamic year calculation from Consumi table is feasible
  - Monitor performance with large datasets (10+ years of 15-minute intervals)

## Query Structure

### Current Files

- `src/pq/CalendarTime.pq`: 15-minute interval calendar with DST handling
- `src/pq/PUN.pq`: Energy price data with DST transitions
- `src/pq/GetLastSundayOfMonth.pq`: Shared DST calculation function
- `src/pq/IT012E00801406.pq`: Consumption data (renamed to Consumi)

### Data Sources

- **GME Data**: `/sources/GME/EE/` - XML files with daily energy market prices
- **CSV Databases**: `/db/` directory containing processed energy data
  - `PUN-MGP.csv`: Prezzo Unico Nazionale (National Single Price)
  - `GAS-MGP.csv`: Gas market prices
  - `PSV_DA.csv`, `PSV_MA.csv`: PSV (Punto di Scambio Virtuale) prices
  - `IT012E00801406.csv`: Individual consumption data

### Power BI Tables

- **CalendarTime**: DateTime (datetimezone), Date, Time, DST columns - 15-minute intervals
- **PUN**: Energy pricing with hourly data and DST handling
- **Consumi**: Energy consumption data (15-minute intervals)
- **Holidays**: Italian public holidays for tariff calculations

### Dashboard Development Areas

- **Cost Analysis**: Real-time consumption cost calculation
- **Usage Patterns**: Peak/off-peak consumption identification
- **Price Correlation**: Consumption timing vs. energy prices
- **Efficiency Metrics**: KPIs for energy optimization
- **Forecasting**: Predictive models for cost planning