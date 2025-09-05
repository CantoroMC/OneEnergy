let
    Source = Table.PromoteHeaders(
        Csv.Document(
            File.Contents(Text.Combine({db, "OneEnergy\GME\PUN-MGP.csv"})),
            [
                Delimiter=";",
                Columns=3,
                Encoding=65001,
                QuoteStyle=QuoteStyle.None
            ]
        ),
        [PromoteAllScalars=true]
    ),
    ChangeTypes = Table.TransformColumnTypes(
        Table.TransformColumnTypes(
            Source, {
                {"Date", type date},
                {"Hour", Int64.Type}
            }
        ),
        {{"PUN", type number}},
        "en-US"
    ),
    AddChangeDates = Table.AddColumn(
        ChangeTypes,
        "IsTimeChangeDay",
        each let
            date = [Date],
            LastSundayOfMonth = (year as number, month as number) as date =>
                let
                    lastDay = Date.EndOfMonth(#date(year, month, 1)),
                    daysToSubtract = Date.DayOfWeek(lastDay, Day.Sunday),
                    lastSunday = Date.AddDays(lastDay, -daysToSubtract)
                in lastSunday,
            year = Date.Year(date),
            lastMarchSunday = LastSundayOfMonth(year, 3),
            lastOctoberSunday = LastSundayOfMonth(year, 10),
            isMarchChange = date = lastMarchSunday,
            isOctoberChange = date = lastOctoberSunday
        in isMarchChange or isOctoberChange,
        type logical
    ),
    MarchChangeDays = Table.SelectRows(AddChangeDates, each [IsTimeChangeDay] and Date.Month([Date]) = 3),
    OctoberChangeDays = Table.SelectRows(AddChangeDates, each [IsTimeChangeDay] and Date.Month([Date]) = 10),
    NormalDays = Table.SelectRows(AddChangeDates, each not [IsTimeChangeDay]),
    AdjustedMarchHours = Table.AddColumn(
        Table.TransformColumns(
            MarchChangeDays,
            {{"Hour", each if _ >= 3 then _ + 1 else _, Int64.Type}}
        ),
        "DSTFlag", each null, type logical
    ),
    AdjustedOctoberHours =
    let
        // Separa ore 1-2: invariate
        Hours1to2 = Table.SelectRows(OctoberChangeDays, each [Hour] <= 2),

        // Hour 3: diventa 2:00 con DST=True (+02:00) - prima occorrenza
        Hour3 = Table.SelectRows(OctoberChangeDays, each [Hour] = 3),
        Hour3Adjusted = Table.TransformColumns(Hour3, {{"Hour", each 2, Int64.Type}}),
        Hour3WithDST = Table.AddColumn(Hour3Adjusted, "DSTFlag", each true, type logical),

        // Hour 4: diventa 2:00 con DST=False (+01:00) - seconda occorrenza
        Hour4 = Table.SelectRows(OctoberChangeDays, each [Hour] = 4),
        Hour4Adjusted = Table.TransformColumns(Hour4, {{"Hour", each 2, Int64.Type}}),
        Hour4WithDST = Table.AddColumn(Hour4Adjusted, "DSTFlag", each false, type logical),

        // Ore 5-25: shift -1 (diventano 4-24)
        Hours5Plus = Table.SelectRows(OctoberChangeDays, each [Hour] >= 5),
        Hours5PlusAdjusted = Table.TransformColumns(Hours5Plus, {{"Hour", each _ - 1, Int64.Type}}),
        Hours5PlusWithDST = Table.AddColumn(Hours5PlusAdjusted, "DSTFlag", each null, type logical),

        // Combina tutto
        Combined = Table.Combine({
            Table.AddColumn(Hours1to2, "DSTFlag", each null, type logical),
            Hour3WithDST,
            Hour4WithDST,
            Hours5PlusWithDST
        })
    in
        Combined,
    CombinedData = Table.Combine({
        Table.AddColumn(NormalDays, "DSTFlag", each null, type logical),
        AdjustedMarchHours,
        AdjustedOctoberHours
    }),
    FinalTable = Table.AddColumn(
        CombinedData,
        "DateTime",
        each
            let
                dstFlag = [DSTFlag],
                hourValue = [Hour]
            in
                if dstFlag = null then
                    let
                        baseDateTime = DateTime.From([Date]) + #duration(0, hourValue-1, 0, 0)
                    in
                        DateTimeZone.From(baseDateTime, "it-IT")
                else if dstFlag = true then
                    #datetimezone(Date.Year([Date]), Date.Month([Date]), Date.Day([Date]), 2, 0, 0, 2, 0) // 2:00 +02:00 (DST)
                else
                    #datetimezone(Date.Year([Date]), Date.Month([Date]), Date.Day([Date]), 2, 0, 0, 1, 0), // 2:00 +01:00 (Standard)
        type datetimezone
    ),
    RemovedColumns = Table.RemoveColumns(FinalTable,{"IsTimeChangeDay", "DSTFlag"}),
    ReorderedColumns = Table.ReorderColumns(RemovedColumns,{"DateTime", "Date", "Hour", "PUN"}),
    ValueType = Table.TransformColumnTypes(ReorderedColumns,{{"PUN", type number}}),
    AddFascia = Table.AddColumn(
        ValueType,
        "Fascia",
        each let
            WeekDay = Date.DayOfWeek([Date], Day.Monday),
            CurrentHour = [Hour],
            IsHoliday = List.Contains(Holidays[HolidayDate], [Date])
        in
            if IsHoliday then "F3"
            else if WeekDay >= 1 and WeekDay <= 5 then // Lun-Ven
                if CurrentHour >= 8 and CurrentHour < 19 then "F1"
                else if (CurrentHour >= 7 and CurrentHour < 8) or (CurrentHour >= 19 and CurrentHour < 23) then "F2"
                else "F3"
            else if WeekDay = 6 then // Sabato
                if CurrentHour >= 7 and CurrentHour < 23 then "F2"
                else "F3"
            else // Domenica sempre F3
                "F3",
        type text
    )
in
    AddFascia