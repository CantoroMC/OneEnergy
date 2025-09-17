let
    Source = Table.PromoteHeaders(
        Csv.Document(
            File.Contents(Text.Combine({db, "IT012E00801406.csv"})),
            [
                Delimiter=";",
                Columns=14,
                Encoding=65001,
                QuoteStyle=QuoteStyle.None
            ]
        ),
        [PromoteAllScalars=true]
    ),
    RemoveUnusedColumns = Table.RemoveColumns(
        Source, {
            "POD",
            "ATTIVA_IMMESSA",
            "REATTIVA_INDUTTIVA_IMMESSA",
            "CONSUMO_REATTIVA_CAPACITIVA_PRELEVATA",
            "REATTIVA_CAPACITIVA_IMMESSA",
            "CONSUMO_PICCO_PRELEVATA",
            "CONSUMO_PICCO_IMMESSA",
            "TIPO_DATO",
            ""
        }),
    ConvertDateColumn = Table.TransformColumnTypes(
        RemoveUnusedColumns,
        {{"DATA", type date}, {"FL_ORA_LEGALE", Int64.Type}}
    ),
    FormatTimeColumn = Table.TransformColumnTypes(
        Table.TransformColumns(
            ConvertDateColumn,
            {{"ORA", each Text.PadStart(_, 6, "0"), type text}}
        ),
        {{"ORA", type time}}
    ),

    FilterValidRecords = Table.SelectRows(
        FormatTimeColumn,
        each 
            let
                IsSpring = [DATA] = GetLastSundayOfMonth(Date.Year([DATA]), 3),
                IsAutumn = [DATA] = GetLastSundayOfMonth(Date.Year([DATA]), 10),
                ShouldExclude = 
                    if IsSpring then
                        // MARZO: Spring forward 02:00 → 03:00
                        // Include FL_ORA_LEGALE=1 only for 00:00-01:45
                        // Include FL_ORA_LEGALE=2 only for 03:00-23:45
                        ([FL_ORA_LEGALE] = 1 and [ORA] >= #time(2, 0, 0)) or
                        ([FL_ORA_LEGALE] = 2 and [ORA] < #time(3, 0, 0))
                    else if IsAutumn then
                        // OTTOBRE: Fall back 03:00 → 02:00  
                        // Include FL_ORA_LEGALE=2 only for 00:00-02:45
                        // Include FL_ORA_LEGALE=1 only for 02:00-23:45
                        ([FL_ORA_LEGALE] = 2 and [ORA] >= #time(3, 0, 0)) or
                        ([FL_ORA_LEGALE] = 1 and [ORA] < #time(2, 0, 0))
                    else
                        // Giorni normali: nessuna esclusione
                        false
            in
                [FL_ORA_LEGALE] <> null
                and [CONSUMO_ATTIVA_PRELEVATA] <> null
                and [CONSUMO_ATTIVA_PRELEVATA] <> ""
                and not ShouldExclude
    ),
    AddDateTime = Table.AddColumn(
        FilterValidRecords,
        "DateTime",
        each
            let
                baseDate = [DATA],
                baseTime = [ORA],
                year = Date.Year(baseDate),
                lastMarchSunday = GetLastSundayOfMonth(year, 3),
                lastOctoberSunday = GetLastSundayOfMonth(year, 10),
                hour = Time.Hour(baseTime),
                minute = Time.Minute(baseTime),
                second = Time.Second(baseTime),
                // Determina il fuso orario basato su data, ora e flag FL_ORA_LEGALE
                timeZoneOffset = 
                    if baseDate > lastMarchSunday and baseDate < lastOctoberSunday then
                        // Periodo estivo DST
                        2
                    else if baseDate = lastMarchSunday and baseTime >= #time(3, 0, 0) then
                        // Giorno cambio marzo: dalle 3:00 in poi è DST
                        2
                    else if baseDate = lastOctoberSunday then
                        // Giorno cambio ottobre: usa FL_ORA_LEGALE per disambiguare
                        if [FL_ORA_LEGALE] = 2 then 2 else 1
                    else
                        // Periodo invernale standard
                        1
            in
                #datetimezone(Date.Year(baseDate), Date.Month(baseDate), Date.Day(baseDate), hour, minute, second, timeZoneOffset, 0),
        type datetimezone
    ),
    AddDateTimeZone = Table.AddColumn(
        AddDateTime,
        "DateTimeZone",
        each
            let
                dateTimeText = DateTime.ToText(DateTime.From([DateTime]), "yyyy-MM-dd HH:mm:ss"),
                timezoneOffset = DateTimeZone.ZoneHours([DateTime]),
                timezoneText = if timezoneOffset >= 0 then "+" & Text.From(timezoneOffset) else Text.From(timezoneOffset)
            in
                dateTimeText & " " & timezoneText & ":00",
        type text
    ),
    FinalCleanup = Table.ReorderColumns(
        Table.RemoveColumns(
            AddDateTimeZone,
            {"DATA", "ORA", "FL_ORA_LEGALE"}
        ), {
            "DateTimeZone",
            "DateTime",
            "CONSUMO_ATTIVA_PRELEVATA",
            "CONSUMO_REATTIVA_INDUTTIVA_PRELEVATA"
        }
    ),
    FormatDataTypes = Table.TransformColumnTypes(
        Table.RenameColumns(
            FinalCleanup, {
            {"CONSUMO_ATTIVA_PRELEVATA", "EE [kWh]"},
            {"CONSUMO_REATTIVA_INDUTTIVA_PRELEVATA", "Q [kVarh]"}
        }),
        {
            {"EE [kWh]", type number},
            {"Q [kVarh]", type number}
        }
    )
in
    FormatDataTypes