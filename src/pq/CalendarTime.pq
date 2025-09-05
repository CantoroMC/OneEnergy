let
    Horizon = TimeHorizon,

    // Genera tutti i quarti d'ora nell'orizzonte temporale
    StartDateTime = DateTime.From(Horizon[StartDate]),
    EndDateTime = DateTime.From(Horizon[EndDate]) + #duration(0, 23, 45, 0),
    QuarterHours = List.DateTimes(
        StartDateTime,
        Duration.TotalMinutes(EndDateTime - StartDateTime) / 15 + 1,
        #duration(0, 0, 15, 0)
    ),

    Source = Table.FromColumns({QuarterHours}, {"DateTime"}),
    ChangedType = Table.TransformColumnTypes(Source,{{"DateTime", type datetime}}),
    AddTime = Table.AddColumn(ChangedType, "Time", each Time.From([DateTime]), type time),
    AddHour = Table.AddColumn(AddTime, "Hour", each Time.Hour([DateTime]), Int64.Type),
    AddDate = Table.AddColumn(AddHour, "Date", each Date.From([DateTime]), type date),
    AddFascia = Table.AddColumn(
        AddDate,
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