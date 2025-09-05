let
    // Calcola l'orizzonte temporale dai dati PUN grezzi
    PUN_Source = Table.PromoteHeaders(
        Csv.Document(
            File.Contents(Text.Combine({db, "GME\PUN-MGP.csv"})),
            [
                Delimiter=";",
                Columns=3,
                Encoding=65001,
                QuoteStyle=QuoteStyle.None
            ]
        ),
        [PromoteAllScalars=true]
    ),
    PUN_Dates = Table.TransformColumnTypes(PUN_Source, {{"Date", type date}})[Date],
    
    StartDate = List.Min(PUN_Dates),
    EndDate = List.Max(PUN_Dates),
    StartYear = Date.Year(StartDate),
    EndYear = Date.Year(EndDate)
in [
    StartDate = StartDate,
    EndDate = EndDate, 
    StartYear = StartYear,
    EndYear = EndYear
]