let
    CalendarBase =
        let
            minY = 2016, //  Date.Year(List.Min(PUN[DateTime])),
            cY = Date.Year(DateTime.LocalNow()),
            DateList = List.Dates(
                #date(minY, 1, 1),
                Duration.TotalDays(#date(cY + 1, 1, 1) - #date(minY, 1, 1)),
                #duration(1, 0, 0, 0)
            ),
            QuarterHourList = {0, 15, 30, 45},
            HourList = {0..23},
            DateTimeRecords = List.Transform(
                DateList,
                (currentDate) =>
                    let
                        year = Date.Year(currentDate),
                        lastMarchSunday = GetLastSundayOfMonth(year, 3),
                        lastOctoberSunday = GetLastSundayOfMonth(year, 10),
                        isMarchTransition = currentDate = lastMarchSunday,
                        isOctoberTransition = currentDate = lastOctoberSunday,
                        TimeSlots =
                            if isMarchTransition then
                                let
                                    AllSlots = List.Combine(
                                        List.Transform(
                                            HourList,
                                            (h) => List.Transform(QuarterHourList, (q) => [Hour = h, Minute = q])
                                        )
                                    )
                                in
                                    List.Select(AllSlots, (slot) => not (slot[Hour] = 2))
                            else if isOctoberTransition then
                                let
                                    AllSlots = List.Combine(
                                        List.Transform(HourList, (h) =>
                                            List.Transform(QuarterHourList, (q) => [Hour = h, Minute = q])
                                        )
                                    ),
                                    NormalSlots = List.Select(AllSlots, (slot) => not (slot[Hour] = 2)),
                                    DuplicatedSlots = List.Combine({
                                        List.Transform(QuarterHourList, (q) => [Hour = 2, Minute = q, DSTFlag = true]),
                                        List.Transform(QuarterHourList, (q) => [Hour = 2, Minute = q, DSTFlag = false])
                                    })
                                in
                                    NormalSlots & DuplicatedSlots
                            else
                                List.Combine(
                                    List.Transform(HourList, (h) =>
                                        List.Transform(QuarterHourList, (q) => [Hour = h, Minute = q])
                                    )
                                ),
                        DateTimeRecords = List.Transform(
                            TimeSlots,
                            (slot) =>
                                let
                                    hour = slot[Hour],
                                    minute = slot[Minute],
                                    dstFlag = if Record.HasFields(slot, "DSTFlag") then slot[DSTFlag] else null,
                                    dateTimeZone =
                                        if dstFlag = null then
                                            let
                                                isDSTPeriod =
                                                    (currentDate > lastMarchSunday and currentDate < lastOctoberSunday) or
                                                    (currentDate = lastMarchSunday and hour >= 3) or
                                                    (currentDate = lastOctoberSunday and hour < 2),
                                                timeZoneOffset = if isDSTPeriod then 2 else 1
                                            in
                                                #datetimezone(Date.Year(currentDate), Date.Month(currentDate), Date.Day(currentDate), hour, minute, 0, timeZoneOffset, 0)
                                        else if dstFlag = true then
                                            #datetimezone(Date.Year(currentDate), Date.Month(currentDate), Date.Day(currentDate), hour, minute, 0, 2, 0)
                                        else
                                            #datetimezone(Date.Year(currentDate), Date.Month(currentDate), Date.Day(currentDate), hour, minute, 0, 1, 0),
                                    dateValue = Date.From(dateTimeZone),
                                    timeValue = Time.From(dateTimeZone),
                                    isDST =
                                        if dstFlag <> null then dstFlag
                                        else DateTimeZone.ZoneHours(dateTimeZone) = 2
                                in
                                    [
                                        DateTime = dateTimeZone,
                                        Date = dateValue,
                                        Time = timeValue,
                                        DST = isDST
                                    ]
                        )
                    in
                        DateTimeRecords
            )
        in
            List.Combine(DateTimeRecords),
    CalendarTable = Table.FromRecords(
        CalendarBase,
        type table [
            DateTime = datetimezone,
            Date = date,
            Time = time,
            DST = logical
        ]
    ),
    SortedTable = Table.Sort(CalendarTable, {"DateTime", Order.Ascending}),
    AddDateTimeZone = Table.ReorderColumns(
        Table.AddColumn(
            SortedTable,
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
        {"DateTimeZone", "DateTime", "Date", "Time", "DST"}
    ),
    AddFascia =
    let
        Holidays = let
            TimeHorizon = let
                StartDate = List.Min(SortedTable[Date]),
                EndDate = List.Max(SortedTable[Date]),
                StartYear = Date.Year(StartDate),
                EndYear = Date.Year(EndDate)
            in
                [
                    StartDate = StartDate,
                    EndDate = EndDate,
                    StartYear = StartYear,
                    EndYear = EndYear
                ],
            Horizon = TimeHorizon,
            StartYear = Horizon[StartYear],
            EndYear = Horizon[EndYear],
            StartDate = Horizon[StartDate],
            EndDate = Horizon[EndDate],
            allDates = List.Dates(StartDate,Duration.TotalDays(EndDate-StartDate)+1,#duration(1,0,0,0)),
            Years = {StartYear .. EndYear},
            holidays = List.Accumulate(
                Years,
                #table({},{}),(state,current) =>
                let
                    Source = Web.Page(Web.Contents("https://www.officeholidays.com/countries/Italy/" & Number.ToText(current))),
                    HolidayTable = Table.SelectRows(Source{0}[Data], each ([Type] = "Public Holiday")),
                    DateCol = Table.SelectColumns(HolidayTable,{"Date","Holiday Name"}),
                    HolidayDate = Table.TransformColumnTypes(
                        Table.AddColumn(
                            DateCol,
                            "HolidayDate",
                            each [Date] & " " & Number.ToText(current)
                        ),
                        { {"HolidayDate", type date} },
                        "en-US"
                    ),
                    CleanUp = Table.RemoveColumns(HolidayDate,{"Date"})
                in
                    state & Table.Distinct(CleanUp)
            )
        in
            holidays,
        Fascia = Table.AddColumn(
            AddDateTimeZone,
            "Fascia",
            each let
                WeekDay = Date.DayOfWeek([Date], Day.Monday),
                CurrentHour = Time.Hour([Time]),
                IsHoliday = List.Contains(Holidays[HolidayDate], [Date])
            in
                if IsHoliday then "F3"
                else if WeekDay >= 0 and WeekDay <= 5 then // Lun-Ven
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
        Fascia
in
    AddFascia