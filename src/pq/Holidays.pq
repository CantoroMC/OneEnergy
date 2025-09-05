let
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
    holidays