import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Calendar, TrendingUp, TrendingDown, Zap, Clock, Euro, Info, Upload, FileText } from 'lucide-react';

// Interfacce TypeScript
interface DataRow {
  data: string;
  ora: number;
  pun: number;
  ora_display?: string;
  fascia?: string;
  fasciaColor?: string;
  fasciaName?: string;
  fasciaBarColor?: string;
  formatted_date?: string;
  samplesCount?: number;
}

interface DailyAverage {
  date: string;
  dateFormatted: string;
  average: number;
  isSelected: boolean;
}

interface CalendarDay {
  day: number;
  isEmpty: boolean;
  available: boolean;
  selected: boolean;
  dateStr?: string;
}

interface CalendarData {
  days: CalendarDay[];
  monthYear: string;
}

const PunChart = () => {
    const [selectedDate, setSelectedDate] = useState('20250917');
    const [csvData, setCsvData] = useState<DataRow[] | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [viewMode, setViewMode] = useState('single');
    const [dateRange, setDateRange] = useState({ start: '', end: '' });
    const [showCalendar, setShowCalendar] = useState(false);
    const [calendarMonth, setCalendarMonth] = useState(0); // 0 = primo mese, 1 = secondo, etc.
    const [calendarYear, setCalendarYear] = useState(0);

    // Dati di default
    const defaultRawData: DataRow[] = [
        {data: "20250917", ora: 1, pun: 106.17947},
        {data: "20250917", ora: 2, pun: 101.95056},
        {data: "20250917", ora: 3, pun: 93.25903},
        {data: "20250917", ora: 4, pun: 102.24588},
        {data: "20250917", ora: 5, pun: 94.96825},
        {data: "20250917", ora: 6, pun: 103.26841},
        {data: "20250917", ora: 7, pun: 115.04726},
        {data: "20250917", ora: 8, pun: 129.22},
        {data: "20250917", ora: 9, pun: 129.70613},
        {data: "20250917", ora: 10, pun: 124.15137},
        {data: "20250917", ora: 11, pun: 116.72992},
        {data: "20250917", ora: 12, pun: 105.92323},
        {data: "20250917", ora: 13, pun: 89.53855},
        {data: "20250917", ora: 14, pun: 88.10792},
        {data: "20250917", ora: 15, pun: 88.70702},
        {data: "20250917", ora: 16, pun: 92.31284},
        {data: "20250917", ora: 17, pun: 100.39173},
        {data: "20250917", ora: 18, pun: 107.35422},
        {data: "20250917", ora: 19, pun: 124.22},
        {data: "20250917", ora: 20, pun: 144.43699},
        {data: "20250917", ora: 21, pun: 136.93387},
        {data: "20250917", ora: 22, pun: 121.04465},
        {data: "20250917", ora: 23, pun: 108.51523},
        {data: "20250917", ora: 24, pun: 106.39141},
        {data: "20250918", ora: 1, pun: 109.61571},
        {data: "20250918", ora: 2, pun: 105.82947},
        {data: "20250918", ora: 3, pun: 103.9874},
        {data: "20250918", ora: 4, pun: 100.77691},
        {data: "20250918", ora: 5, pun: 100.65138},
        {data: "20250918", ora: 6, pun: 104.37091},
        {data: "20250918", ora: 7, pun: 117.12721},
        {data: "20250918", ora: 8, pun: 135.0},
        {data: "20250918", ora: 9, pun: 131.89},
        {data: "20250918", ora: 10, pun: 108.82283},
        {data: "20250918", ora: 11, pun: 108.33},
        {data: "20250918", ora: 12, pun: 95.73},
        {data: "20250918", ora: 13, pun: 80.64},
        {data: "20250918", ora: 14, pun: 79.23},
        {data: "20250918", ora: 15, pun: 86.28},
        {data: "20250918", ora: 16, pun: 95.73},
        {data: "20250918", ora: 17, pun: 108.4777},
        {data: "20250918", ora: 18, pun: 117.45166},
        {data: "20250918", ora: 19, pun: 128.97},
        {data: "20250918", ora: 20, pun: 174.0},
        {data: "20250918", ora: 21, pun: 146.83},
        {data: "20250918", ora: 22, pun: 120.3},
        {data: "20250918", ora: 23, pun: 115.0},
        {data: "20250918", ora: 24, pun: 110.91},
        // Dati novembre 2024
        {data: "20241101", ora: 1, pun: 95.50},
        {data: "20241101", ora: 2, pun: 90.25},
        {data: "20241101", ora: 8, pun: 125.30},
        {data: "20241101", ora: 12, pun: 110.75},
        {data: "20241101", ora: 18, pun: 140.20},
        {data: "20241101", ora: 24, pun: 100.15},
        // Dati gennaio 2025
        {data: "20250115", ora: 1, pun: 88.30},
        {data: "20250115", ora: 8, pun: 118.45},
        {data: "20250115", ora: 12, pun: 105.60},
        {data: "20250115", ora: 18, pun: 135.80},
        {data: "20250115", ora: 24, pun: 95.25},
        // Dati marzo 2025
        {data: "20250320", ora: 1, pun: 92.70},
        {data: "20250320", ora: 8, pun: 122.90},
        {data: "20250320", ora: 12, pun: 108.40},
        {data: "20250320", ora: 18, pun: 138.60},
        {data: "20250320", ora: 24, pun: 98.85}
    ];
    const rawData = csvData || defaultRawData;

    // Upload CSV
    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            setError('Per favore seleziona un file CSV');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            const text = await new Promise<string>((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target?.result as string);
                reader.onerror = reject;
                reader.readAsText(file);
            });

            const lines = text.trim().split('\n');

            const header = lines[0];
            if (!header.includes('Date;Hour;PUN')) {
                throw new Error('Formato CSV non valido. Header atteso: Date;Hour;PUN');
            }

            const parsedData: DataRow[] = [];
            for (let i = 1; i < lines.length; i++) {
                const line = lines[i].trim();
                if (!line) continue;

                const values = line.split(';');
                if (values.length !== 3) {
                    throw new Error(`Riga ${i + 1}: formato non valido`);
                }

                const [date, hour, punStr] = values;
                const punValue = parseFloat(punStr.replace(',', '.'));

                if (isNaN(punValue)) {
                    throw new Error(`Riga ${i + 1}: valore PUN non valido`);
                }

                parsedData.push({
                    data: date,
                    ora: parseInt(hour),
                    pun: punValue
                });
            }

            setCsvData(parsedData);
            setSelectedDate(parsedData[0].data);

        } catch (err: any) {
            setError(`Errore: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Processo dati
    const processedData = rawData.map(row => {
        let fascia = 'F3';
        let fasciaColor = '#10B981';
        let fasciaName = 'F3 - Fuori Punta';
        let fasciaBarColor = '#10B981';

        if (row.ora >= 8 && row.ora <= 19) {
            fascia = 'F1';
            fasciaColor = '#EF4444';
            fasciaName = 'F1 - Punta';
            fasciaBarColor = '#EF4444';
        } else if ((row.ora >= 7 && row.ora < 8) || (row.ora >= 20 && row.ora <= 23)) {
            fascia = 'F2';
            fasciaColor = '#F59E0B';
            fasciaName = 'F2 - Intermedia';
            fasciaBarColor = '#F59E0B';
        }
        return {
            ...row,
            ora_display: `${row.ora.toString().padStart(2, '0')}:00`,
            fascia,
            fasciaColor,
            fasciaName,
            fasciaBarColor,
            formatted_date: `${row.data.substring(6,8)}/${row.data.substring(4,6)}/${row.data.substring(0,4)}`
        };
    });

    const availableDates = [...new Set(rawData.map(d => d.data))].sort();

    useEffect(() => {
        if (availableDates.length > 0) {
            setDateRange({ start: availableDates[0], end: availableDates[availableDates.length - 1] });
        }
    }, [availableDates.length]);

    // Calcolo dati filtrati
    const filteredData = useCallback(() => {
        if (viewMode === 'single') {
            return processedData.filter(d => d.data === selectedDate);
        } else {
            const startIndex = availableDates.indexOf(dateRange.start);
            const endIndex = availableDates.indexOf(dateRange.end);
            const selectedDates = availableDates.slice(startIndex, endIndex + 1);
            const hourlyAverages: DataRow[] = [];

            for (let hour = 1; hour <= 24; hour++) {
                const hourData: number[] = [];
                selectedDates.forEach(date => {
                    const dayHourData = processedData.find(d => d.data === date && d.ora === hour);
                    if (dayHourData) {
                        hourData.push(dayHourData.pun);
                    }
                });

                if (hourData.length > 0) {
                    const avgPun = hourData.reduce((sum, val) => sum + val, 0) / hourData.length;

                    let fascia = 'F3';
                    let fasciaColor = '#10B981';
                    let fasciaName = 'F3 - Fuori Punta';
                    let fasciaBarColor = '#10B981';

                    if (hour >= 8 && hour <= 19) {
                        fascia = 'F1';
                        fasciaColor = '#EF4444';
                        fasciaName = 'F1 - Punta';
                        fasciaBarColor = '#EF4444';
                    } else if ((hour >= 7 && hour < 8) || (hour >= 20 && hour <= 23)) {
                        fascia = 'F2';
                        fasciaColor = '#F59E0B';
                        fasciaName = 'F2 - Intermedia';
                        fasciaBarColor = '#F59E0B';
                    }

                    hourlyAverages.push({
                        data: 'range',
                        ora: hour,
                        pun: avgPun,
                        ora_display: `${hour.toString().padStart(2, '0')}:00`,
                        fascia,
                        fasciaColor,
                        fasciaName,
                        fasciaBarColor,
                        samplesCount: hourData.length
                    });
                }
            }
            return hourlyAverages;
        }
    }, [viewMode, selectedDate, processedData, availableDates, dateRange])();

    // Calcolo intervallo dinamico
    const punValues = filteredData.map(d => d.pun);
    const dataMin = Math.min(...punValues);
    const dataMax = Math.max(...punValues);
    const range = dataMax - dataMin;
    const padding = range * 0.1;

    const yMinRaw = Math.max(0, dataMin - padding);
    const yMaxRaw = dataMax + padding;

    const yMin = Math.floor(yMinRaw / 5) * 5;
    const yMax = Math.ceil(yMaxRaw / 5) * 5;

    // Statistiche
    const stats = {
        min: Math.min(...filteredData.map(d => d.pun)),
        max: Math.max(...filteredData.map(d => d.pun)),
        avg: filteredData.reduce((sum, d) => sum + d.pun, 0) / filteredData.length,
        range: Math.max(...filteredData.map(d => d.pun)) - Math.min(...filteredData.map(d => d.pun)),
        f1_avg: filteredData.filter(d => d.fascia === 'F1').reduce((sum, d) => sum + d.pun, 0) / (filteredData.filter(d => d.fascia === 'F1').length || 1),
        f2_avg: filteredData.filter(d => d.fascia === 'F2').reduce((sum, d) => sum + d.pun, 0) / (filteredData.filter(d => d.fascia === 'F2').length || 1),
        f3_avg: filteredData.filter(d => d.fascia === 'F3').reduce((sum, d) => sum + d.pun, 0) / (filteredData.filter(d => d.fascia === 'F3').length || 1)
    };

    // Overview dati
    const dailyAverages: DailyAverage[] = availableDates.map((date, index) => {
        const dayData = processedData.filter(d => d.data === date);
        const average = dayData.reduce((sum, d) => sum + d.pun, 0) / dayData.length;

        let isHighlighted = false;
        if (viewMode === 'single') {
            isHighlighted = date === selectedDate;
        } else {
            const startIndex = availableDates.indexOf(dateRange.start);
            const endIndex = availableDates.indexOf(dateRange.end);
            isHighlighted = index >= startIndex && index <= endIndex;
        }

        return {
            date: date,
            dateFormatted: `${date.substring(6, 8)}/${date.substring(4, 6)}`,
            average: average,
            isSelected: isHighlighted
        };
    });

    const handleDayClick = (data: any) => {
        console.log('Click data:', data); // Debug
        if (viewMode === 'single' && data && data.activePayload) {
            const clickedData = data.activePayload[0]?.payload as DailyAverage;
            console.log('Clicked data:', clickedData); // Debug
            if (clickedData && clickedData.date) {
                setSelectedDate(clickedData.date);
            }
        }
    };

    // Funzione per creare il mini calendario
    // Calcola i mesi/anni disponibili dai dati
    const getAvailableMonthsYears = () => {
        if (availableDates.length === 0) return [];

        const monthsYears = new Set<string>();
        availableDates.forEach(date => {
            const year = date.substring(0, 4);
            const month = date.substring(4, 6);
            monthsYears.add(`${year}-${month}`);
        });

        return Array.from(monthsYears).sort();
    };

    const availableMonthsYears = getAvailableMonthsYears();

    // Inizializza il calendario al primo mese disponibile
    useEffect(() => {
        if (availableMonthsYears.length > 0 && calendarMonth === 0 && calendarYear === 0) {
            // Usa il mese del selectedDate se disponibile, altrimenti il primo
            if (selectedDate) {
                const selectedYear = selectedDate.substring(0, 4);
                const selectedMonth = selectedDate.substring(4, 6);
                const targetMonthYear = `${selectedYear}-${selectedMonth}`;
                const index = availableMonthsYears.indexOf(targetMonthYear);
                if (index !== -1) {
                    setCalendarMonth(index);
                    setCalendarYear(0);
                    return;
                }
            }
            setCalendarMonth(0);
            setCalendarYear(0);
        }
    }, [availableMonthsYears.length, selectedDate]);

    const createCalendarData = (): CalendarData => {
        if (availableMonthsYears.length === 0) return { days: [], monthYear: '' };

        const currentMonthYear = availableMonthsYears[calendarMonth] || availableMonthsYears[0];
        const [yearStr, monthStr] = currentMonthYear.split('-');
        const year = parseInt(yearStr);
        const month = parseInt(monthStr);

        const monthNames = [
            'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
            'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'
        ];

        // Calcola primo giorno del mese e numero di giorni
        const firstDayOfMonth = new Date(year, month - 1, 1);
        const lastDayOfMonth = new Date(year, month, 0);
        const daysInMonth = lastDayOfMonth.getDate();
        const startingDayOfWeek = firstDayOfMonth.getDay();

        const days: CalendarDay[] = [];

        // Aggiungi giorni vuoti per allineare il calendario
        for (let i = 0; i < startingDayOfWeek; i++) {
            days.push({ day: 0, isEmpty: true, available: false, selected: false });
        }

        // Aggiungi i giorni del mese
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}${month.toString().padStart(2, '0')}${day.toString().padStart(2, '0')}`;
            const isAvailable = availableDates.includes(dateStr);

            let isSelected = false;
            if (viewMode === 'single') {
                isSelected = dateStr === selectedDate;
            } else {
                // Modalità range: evidenzia il range selezionato
                if (dateRange.start && dateRange.end) {
                    const startIndex = availableDates.indexOf(dateRange.start);
                    const endIndex = availableDates.indexOf(dateRange.end);
                    const currentIndex = availableDates.indexOf(dateStr);
                    isSelected = currentIndex >= startIndex && currentIndex <= endIndex;
                } else if (dateRange.start) {
                    isSelected = dateStr === dateRange.start;
                }
            }

            days.push({
                day: day,
                isEmpty: false,
                available: isAvailable,
                selected: isSelected,
                dateStr: dateStr
            });
        }

        return {
            days: days,
            monthYear: `${monthNames[month - 1]} ${year}`
        };
    };

    const navigateCalendar = (direction: 'prev' | 'next') => {
        if (direction === 'prev' && calendarMonth > 0) {
            setCalendarMonth(calendarMonth - 1);
        } else if (direction === 'next' && calendarMonth < availableMonthsYears.length - 1) {
            setCalendarMonth(calendarMonth + 1);
        }
    };

    const handleRangeChange = (type: 'start' | 'end', dateStr: string) => {
        setDateRange(prev => {
            const newRange = { ...prev, [type]: dateStr };
            const startIndex = availableDates.indexOf(newRange.start);
            const endIndex = availableDates.indexOf(newRange.end);

            if (startIndex > endIndex && startIndex !== -1 && endIndex !== -1) {
                if (type === 'start') {
                    newRange.end = newRange.start;
                } else {
                    newRange.start = newRange.end;
                }
            }
            return newRange;
        });
    };

    const handleDateClick = (dateStr: string) => {
        if (availableDates.includes(dateStr)) {
            if (viewMode === 'single') {
                setSelectedDate(dateStr);
                setShowCalendar(false);
            } else {
                // Modalità range: gestione selezione inizio/fine
                if (!dateRange.start || (dateRange.start && dateRange.end)) {
                    // Prima selezione o reset
                    setDateRange({ start: dateStr, end: '' });
                } else if (dateRange.start && !dateRange.end) {
                    // Seconda selezione
                    const startIndex = availableDates.indexOf(dateRange.start);
                    const endIndex = availableDates.indexOf(dateStr);

                    if (startIndex <= endIndex) {
                        setDateRange(prev => ({ ...prev, end: dateStr }));
                    } else {
                        setDateRange({ start: dateStr, end: dateRange.start });
                    }
                    setShowCalendar(false);
                }
            }
        }
    };

    const calendarData = createCalendarData();

    // Interfaccia per il tooltip
    interface CustomTooltipProps {
        active?: boolean;
        payload?: any[];
        label?: string;
    }

    const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;

            return (
                <div className="bg-white p-3 border border-gray-300 rounded-lg shadow-lg">
                    <p className="font-semibold">{`Ora: ${label}`}</p>
                    <p className="text-blue-600">
                        {`PUN: ${data.pun.toFixed(2)} €/MWh`}
                        {viewMode === 'range' && data.samplesCount && (
                            <span className="text-xs text-gray-500 block">
                                Media su {data.samplesCount} giorni
                            </span>
                        )}
                    </p>
                    <p className={`text-sm font-medium`} style={{ color: data.fasciaColor }}>
                        {data.fasciaName}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center">
                        <Zap className="mr-3 text-yellow-500" />
                        Prezzo Medio Orario PUN
                    </h1>
                    <p className="text-gray-600 text-lg">
                        Andamento del Prezzo Unico Nazionale dell'energia elettrica in Italia
                    </p>
                </div>

                {/* Layout Overview - ALTEZZA FISSA 400px */}
                <div className="flex gap-8 mb-8" style={{ height: '400px' }}>
                    {/* Controlli 25% */}
                    <div className="w-1/4 h-full">
                        <div className="bg-white rounded-xl shadow-lg p-4 h-full flex flex-col">
                            {/* Upload */}
                            <div className="mb-4 flex-shrink-0">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    <Upload className="inline w-4 h-4 mr-1" />
                                    Carica CSV
                                </label>
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={handleFileUpload}
                                    disabled={isLoading}
                                    className="w-full text-xs p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                                {isLoading && (
                                    <div className="flex items-center mt-1">
                                        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
                                        <span className="text-xs text-gray-600">Caricamento...</span>
                                    </div>
                                )}
                                {csvData && (
                                    <p className="text-xs text-green-600 mt-1">
                                        <FileText className="w-3 h-3 mr-1 inline" />
                                        {csvData.length} righe ({availableDates.length} giorni)
                                    </p>
                                )}
                                {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
                            </div>

                            {/* Toggle */}
                            <div className="mb-4 flex-shrink-0">
                                <label className="block text-sm font-medium text-gray-700 mb-2">Modalità</label>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => setViewMode('single')}
                                        className={`flex items-center px-3 py-1 rounded-lg text-xs ${viewMode === 'single' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                                            }`}
                                    >
                                        <Calendar className="w-3 h-3 mr-1" />
                                        Singolo
                                    </button>
                                    <button
                                        onClick={() => setViewMode('range')}
                                        className={`flex items-center px-3 py-1 rounded-lg text-xs ${viewMode === 'range' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                                            }`}
                                    >
                                        <TrendingUp className="w-3 h-3 mr-1" />
                                        Periodo
                                    </button>
                                </div>
                            </div>

                            {/* Controlli Principali - FLEX-1 per espandersi */}
                            <div className="flex-1 min-h-0">
                                {viewMode === 'single' ? (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            <Calendar className="inline w-4 h-4 mr-1" />
                                            Data Selezionata
                                        </label>

                                        {/* Bottone Date Picker */}
                                        <div className="relative">
                                            <button
                                                onClick={() => setShowCalendar(!showCalendar)}
                                                className="w-full text-left p-2 border border-gray-300 rounded-lg bg-white hover:border-blue-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span>
                                                        {selectedDate ?
                                                            `${selectedDate.substring(6, 8)}/${selectedDate.substring(4, 6)}/${selectedDate.substring(0, 4)}`
                                                            : 'Seleziona data'
                                                        }
                                                    </span>
                                                    <Calendar className="w-4 h-4 text-gray-400" />
                                                </div>
                                            </button>

                                            {/* Popup Calendario */}
                                            {showCalendar && (
                                                <div className="absolute top-full left-0 z-50 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-3 w-72">
                                                    {/* Header con navigazione */}
                                                    <div className="flex items-center justify-between mb-2">
                                                        <button
                                                            onClick={() => navigateCalendar('prev')}
                                                            disabled={calendarMonth === 0}
                                                            className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                                            </svg>
                                                        </button>

                                                        <div className="text-center flex-1">
                                                            <h4 className="text-sm font-semibold text-gray-800">
                                                                {calendarData.monthYear}
                                                            </h4>
                                                        </div>

                                                        <button
                                                            onClick={() => navigateCalendar('next')}
                                                            disabled={calendarMonth === availableMonthsYears.length - 1}
                                                            className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                            </svg>
                                                        </button>
                                                    </div>

                                                    {/* Indicatore posizione */}
                                                    <div className="text-center mb-2">
                                                        <div className="text-xs text-gray-500">
                                                            {calendarMonth + 1} di {availableMonthsYears.length} mesi
                                                        </div>
                                                    </div>

                                                    {/* Header giorni della settimana */}
                                                    <div className="grid grid-cols-7 gap-1 mb-2">
                                                        {['D', 'L', 'M', 'M', 'G', 'V', 'S'].map(day => (
                                                            <div key={day} className="text-xs font-medium text-gray-600 text-center p-1">
                                                                {day}
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {/* Griglia calendario */}
                                                    <div className="grid grid-cols-7 gap-1">
                                                        {calendarData.days.map((dayInfo, index) => (
                                                            <button
                                                                key={index}
                                                                onClick={() => dayInfo.available && handleDateClick(dayInfo.dateStr!)}
                                                                disabled={!dayInfo.available || dayInfo.isEmpty}
                                                                className={`
                                  text-xs p-1.5 rounded transition-colors h-8 w-8
                                  ${dayInfo.isEmpty ? 'invisible' : ''}
                                  ${!dayInfo.available ? 'text-gray-300 cursor-not-allowed' : ''}
                                  ${dayInfo.available && !dayInfo.selected ? 'text-gray-700 hover:bg-blue-100 cursor-pointer' : ''}
                                  ${dayInfo.selected ? 'bg-blue-500 text-white font-semibold' : ''}
                                  ${dayInfo.available && !dayInfo.selected ? 'bg-gray-50 hover:bg-blue-50 border border-gray-200' : ''}
                                `}
                                                            >
                                                                {dayInfo.day}
                                                            </button>
                                                        ))}
                                                    </div>

                                                    {/* Footer con close */}
                                                    <div className="mt-3 pt-2 border-t border-gray-100 flex justify-between items-center">
                                                        <div className="text-xs text-gray-500">
                                                            {availableDates.length} giorni disponibili
                                                        </div>
                                                        <button
                                                            onClick={() => setShowCalendar(false)}
                                                            className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                                                        >
                                                            Chiudi
                                                        </button>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Overlay per chiudere il calendario */}
                                            {showCalendar && (
                                                <div
                                                    className="fixed inset-0 z-40"
                                                    onClick={() => setShowCalendar(false)}
                                                />
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            <Clock className="inline w-4 h-4 mr-1" />
                                            Periodo (Media Oraria)
                                        </label>

                                        {/* Bottone Date Picker per Range */}
                                        <div className="relative flex-1">
                                            <button
                                                onClick={() => setShowCalendar(!showCalendar)}
                                                className="w-full text-left p-2 border border-gray-300 rounded-lg bg-white hover:border-blue-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm mb-2"
                                            >
                                                <div className="flex items-center justify-between">
                                                    <span>
                                                        {dateRange.start && dateRange.end ?
                                                            `${dateRange.start.substring(6, 8)}/${dateRange.start.substring(4, 6)} - ${dateRange.end.substring(6, 8)}/${dateRange.end.substring(4, 6)}`
                                                            : dateRange.start ?
                                                                `Dal ${dateRange.start.substring(6, 8)}/${dateRange.start.substring(4, 6)} - Seleziona fine`
                                                                : 'Seleziona periodo'
                                                        }
                                                    </span>
                                                    <Calendar className="w-4 h-4 text-gray-400" />
                                                </div>
                                            </button>

                                            {dateRange.start && dateRange.end && (
                                                <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                                                    <Clock className="inline w-3 h-3 mr-1" />
                                                    {availableDates.indexOf(dateRange.end) - availableDates.indexOf(dateRange.start) + 1} giorni
                                                </div>
                                            )}

                                            {/* Popup Calendario per Range */}
                                            {showCalendar && (
                                                <div className="absolute top-full left-0 z-50 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-3 w-72">
                                                    {/* Header con navigazione */}
                                                    <div className="flex items-center justify-between mb-2">
                                                        <button
                                                            onClick={() => navigateCalendar('prev')}
                                                            disabled={calendarMonth === 0}
                                                            className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                                            </svg>
                                                        </button>

                                                        <div className="text-center flex-1">
                                                            <h4 className="text-sm font-semibold text-gray-800">
                                                                {calendarData.monthYear}
                                                            </h4>
                                                            <p className="text-xs text-blue-600 mt-1">
                                                                {!dateRange.start ? 'Seleziona data inizio' :
                                                                 !dateRange.end ? 'Seleziona data fine' : 'Periodo selezionato'}
                                                            </p>
                                                        </div>

                                                        <button
                                                            onClick={() => navigateCalendar('next')}
                                                            disabled={calendarMonth === availableMonthsYears.length - 1}
                                                            className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                            </svg>
                                                        </button>
                                                    </div>

                                                    {/* Indicatore posizione */}
                                                    <div className="text-center mb-2">
                                                        <div className="text-xs text-gray-500">
                                                            {calendarMonth + 1} di {availableMonthsYears.length} mesi
                                                        </div>
                                                    </div>

                                                    {/* Header giorni della settimana */}
                                                    <div className="grid grid-cols-7 gap-1 mb-2">
                                                        {['D', 'L', 'M', 'M', 'G', 'V', 'S'].map(day => (
                                                            <div key={day} className="text-xs font-medium text-gray-600 text-center p-1">
                                                                {day}
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {/* Griglia calendario */}
                                                    <div className="grid grid-cols-7 gap-1">
                                                        {calendarData.days.map((dayInfo, index) => {
                                                            let dayClass = 'text-xs p-1.5 rounded transition-colors h-8 w-8';

                                                            if (dayInfo.isEmpty) {
                                                                dayClass += ' invisible';
                                                            } else if (!dayInfo.available) {
                                                                dayClass += ' text-gray-300 cursor-not-allowed';
                                                            } else if (dayInfo.selected) {
                                                                if (dayInfo.dateStr === dateRange.start || dayInfo.dateStr === dateRange.end) {
                                                                    dayClass += ' bg-blue-500 text-white font-semibold';
                                                                } else {
                                                                    dayClass += ' bg-blue-200 text-blue-800';
                                                                }
                                                            } else {
                                                                dayClass += ' text-gray-700 hover:bg-blue-100 cursor-pointer bg-gray-50 hover:bg-blue-50 border border-gray-200';
                                                            }

                                                            return (
                                                                <button
                                                                    key={index}
                                                                    onClick={() => dayInfo.available && handleDateClick(dayInfo.dateStr!)}
                                                                    disabled={!dayInfo.available || dayInfo.isEmpty}
                                                                    className={dayClass}
                                                                >
                                                                    {dayInfo.day}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>

                                                    {/* Footer con reset e close */}
                                                    <div className="mt-3 pt-2 border-t border-gray-100 flex justify-between items-center">
                                                        <button
                                                            onClick={() => setDateRange({ start: '', end: '' })}
                                                            className="text-xs text-red-600 hover:text-red-700 font-medium"
                                                        >
                                                            Reset
                                                        </button>
                                                        <div className="text-xs text-gray-500">
                                                            {availableDates.length} giorni disponibili
                                                        </div>
                                                        <button
                                                            onClick={() => setShowCalendar(false)}
                                                            className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                                                        >
                                                            Chiudi
                                                        </button>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Overlay per chiudere il calendario */}
                                            {showCalendar && (
                                                <div
                                                    className="fixed inset-0 z-40"
                                                    onClick={() => setShowCalendar(false)}
                                                />
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Overview 75% */}
                    <div className="w-3/4 h-full">
                        <div className="bg-white rounded-xl shadow-lg p-6 h-full flex flex-col">
                            <div className="mb-4 flex-shrink-0">
                                <h3 className="text-lg font-bold text-gray-900 flex items-center">
                                    <TrendingUp className="mr-2 text-blue-500" />
                                    {viewMode === 'single' ? 'Media PUN Giornaliera' : 'Overview Periodo Selezionato'}
                                </h3>
                            </div>

                            {/* Grafico che occupa tutto lo spazio rimanente */}
                            <div className="flex-1 min-h-0">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart
                                        data={dailyAverages}
                                        margin={{ top: 10, right: 10, left: 10, bottom: 40 }}
                                        onClick={handleDayClick}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                        <XAxis
                                            dataKey="dateFormatted"
                                            tick={{ fontSize: 11 }}
                                            axisLine={{ stroke: '#9CA3AF' }}
                                        />
                                        <YAxis
                                            tick={{ fontSize: 11 }}
                                            axisLine={{ stroke: '#9CA3AF' }}
                                            width={40}
                                        />
                                        <Tooltip
                                            formatter={(value: number) => [`${value.toFixed(1)} €/MWh`, 'Media PUN']}
                                            labelFormatter={(label) => `Data: ${label}`}
                                        />
                                        <Bar
                                            dataKey="average"
                                            radius={[2, 2, 0, 0]}
                                            cursor="pointer"
                                        >
                                            {dailyAverages.map((entry, index) => (
                                                <Cell
                                                    key={`cell-${index}`}
                                                    fill={entry.isSelected ? '#3B82F6' : '#93C5FD'}
                                                    stroke={entry.isSelected ? '#1E40AF' : '#3B82F6'}
                                                    strokeWidth={entry.isSelected ? 2 : 0}
                                                />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="mt-2 flex-shrink-0">
                                <p className="text-xs text-gray-500 text-center">
                                    {viewMode === 'single'
                                        ? 'Clicca su una barra per visualizzare il dettaglio orario del giorno'
                                        : 'Visualizzazione delle medie giornaliere con evidenziato il periodo selezionato'
                                    }
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Statistiche */}
                <div className="flex flex-wrap gap-4 mb-8">
                    <div className="flex-1 min-w-[200px] bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Prezzo Minimo</p>
                                <p className="text-2xl font-bold text-green-600">{stats.min.toFixed(2)}</p>
                                <p className="text-xs text-gray-500">€/MWh</p>
                            </div>
                            <TrendingDown className="w-8 h-8 text-green-500 flex-shrink-0" />
                        </div>
                    </div>

                    <div className="flex-1 min-w-[200px] bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Prezzo Massimo</p>
                                <p className="text-2xl font-bold text-red-600">{stats.max.toFixed(2)}</p>
                                <p className="text-xs text-gray-500">€/MWh</p>
                            </div>
                            <TrendingUp className="w-8 h-8 text-red-500 flex-shrink-0" />
                        </div>
                    </div>

                    <div className="flex-1 min-w-[200px] bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Prezzo Medio</p>
                                <p className="text-2xl font-bold text-blue-600">{stats.avg.toFixed(2)}</p>
                                <p className="text-xs text-gray-500">€/MWh</p>
                            </div>
                            <Euro className="w-8 h-8 text-blue-500 flex-shrink-0" />
                        </div>
                    </div>

                    <div className="flex-1 min-w-[200px] bg-white rounded-xl shadow-lg p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Variazione</p>
                                <p className="text-2xl font-bold text-purple-600">{stats.range.toFixed(2)}</p>
                                <p className="text-xs text-gray-500">Range giornaliero</p>
                            </div>
                            <Clock className="w-8 h-8 text-purple-500 flex-shrink-0" />
                        </div>
                    </div>
                </div>

                {/* Analisi Fasce */}
                <div className="flex flex-wrap gap-4 mb-8">
                    <div className="flex-1 min-w-[250px] p-6 border-l-4 border-red-500 bg-red-50 rounded-xl shadow-lg">
                        <h4 className="font-semibold text-red-700 mb-2">F1 - Fascia di Punta</h4>
                        <p className="text-sm text-gray-600 mb-2">Lun-Ven: 08:00-19:00</p>
                        <p className="text-2xl font-bold text-red-600">{stats.f1_avg.toFixed(2)} €/MWh</p>
                        <p className="text-xs text-gray-500">Prezzo medio fascia</p>
                    </div>

                    <div className="flex-1 min-w-[250px] p-6 border-l-4 border-yellow-500 bg-yellow-50 rounded-xl shadow-lg">
                        <h4 className="font-semibold text-yellow-700 mb-2">F2 - Fascia Intermedia</h4>
                        <p className="text-sm text-gray-600 mb-2">Lun-Ven: 07:00-08:00, 19:00-23:00</p>
                        <p className="text-2xl font-bold text-yellow-600">{stats.f2_avg.toFixed(2)} €/MWh</p>
                        <p className="text-xs text-gray-500">Prezzo medio fascia</p>
                    </div>

                    <div className="flex-1 min-w-[250px] p-6 border-l-4 border-green-500 bg-green-50 rounded-xl shadow-lg">
                        <h4 className="font-semibold text-green-700 mb-2">F3 - Fascia Fuori Punta</h4>
                        <p className="text-sm text-gray-600 mb-2">Lun-Sab: 00:00-07:00, 23:00-24:00</p>
                        <p className="text-2xl font-bold text-green-600">{stats.f3_avg.toFixed(2)} €/MWh</p>
                        <p className="text-xs text-gray-500">Prezzo medio fascia</p>
                    </div>
                </div>

                {/* Grafico Principale */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-2xl font-bold text-gray-900">
                            {viewMode === 'single'
                                ? `Andamento Orario - ${selectedDate.substring(6, 8)}/${selectedDate.substring(4, 6)}/${selectedDate.substring(0, 4)}`
                                : `Media Oraria Periodo - ${dateRange.start?.substring(6, 8)}/${dateRange.start?.substring(4, 6)} → ${dateRange.end?.substring(6, 8)}/${dateRange.end?.substring(4, 6)}`
                            }
                        </h2>
                        <div className="text-sm text-gray-600">Fonte: GME</div>
                    </div>

                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={filteredData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                            <XAxis
                                dataKey="ora_display"
                                tick={{ fontSize: 12 }}
                                axisLine={{ stroke: '#9CA3AF' }}
                            />
                            <YAxis
                                tick={{ fontSize: 12 }}
                                axisLine={{ stroke: '#9CA3AF' }}
                                domain={[yMin, yMax]}
                                label={{
                                    value: '€/MWh',
                                    angle: -90,
                                    position: 'insideLeft',
                                    style: { textAnchor: 'middle' }
                                }}
                            />
                            <Tooltip
                                content={<CustomTooltip />}
                                contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid #D1D5DB',
                                    borderRadius: '8px',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                }}
                            />
                            <Legend />

                            <Bar
                                dataKey="pun"
                                name="PUN (€/MWh)"
                                radius={[2, 2, 0, 0]}
                            >
                                {filteredData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={entry.fasciaBarColor}
                                        fillOpacity={0.8}
                                        stroke={entry.fasciaBarColor}
                                        strokeWidth={1}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default PunChart;