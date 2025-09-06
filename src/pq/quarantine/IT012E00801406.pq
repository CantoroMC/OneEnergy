let
    Source = Table.PromoteHeaders(
        Csv.Document(
            File.Contents(Text.Combine({db, "DSO\IT012E00801406.csv"})),
            [
                Delimiter=";",
                Columns=14,
                Encoding=65001,
                QuoteStyle=QuoteStyle.None
            ]
        ),
        [PromoteAllScalars=true]
    ),
    RemoveUnusedColumns = Table.RemoveColumns(Source,{"POD", "ATTIVA_IMMESSA", "REATTIVA_INDUTTIVA_IMMESSA", "CONSUMO_REATTIVA_CAPACITIVA_PRELEVATA", "REATTIVA_CAPACITIVA_IMMESSA", "CONSUMO_PICCO_PRELEVATA", "CONSUMO_PICCO_IMMESSA", "TIPO_DATO", ""}),
    ConvertDateColumn = Table.TransformColumnTypes(RemoveUnusedColumns,{{"DATA", type date}}),
    PadTimeColumn = Table.TransformColumns(ConvertDateColumn, {{"ORA", each Text.PadStart(_, 6, "0"), type text}}),
    ConvertTimeColumn = Table.TransformColumnTypes(PadTimeColumn,{{"ORA", type time}}),

    // Filtra solo i record validi usando FL_ORA_LEGALE
    // I record non validi hanno FL_ORA_LEGALE=null o valori di consumo nulli
    FilterValidRecords = Table.SelectRows(
        ConvertTimeColumn,
        each [FL_ORA_LEGALE] <> null
             and [CONSUMO_ATTIVA_PRELEVATA] <> null
             and [CONSUMO_ATTIVA_PRELEVATA] <> ""
    ),

    // Crea DateTime combinando DATA e ORA
    AddDateTime = Table.AddColumn(
        FilterValidRecords,
        "DateTime",
        each DateTime.From([DATA]) + #duration(0, Time.Hour([ORA]), Time.Minute([ORA]), Time.Second([ORA])),
        type datetime
    ),

    // Rimuove le colonne non più necessarie e mantiene solo DateTime
    FinalCleanup = Table.RemoveColumns(AddDateTime, {"DATA", "ORA", "FL_ORA_LEGALE"}),

    // Riordina le colonne
    ReorderedColumns = Table.ReorderColumns(FinalCleanup, {"DateTime", "CONSUMO_ATTIVA_PRELEVATA", "CONSUMO_REATTIVA_INDUTTIVA_PRELEVATA"}),

    // Rinomina le colonne di consumo
    RenamedColumns = Table.RenameColumns(ReorderedColumns, {
        {"CONSUMO_ATTIVA_PRELEVATA", "EE [kWh]"},
        {"CONSUMO_REATTIVA_INDUTTIVA_PRELEVATA", "Q [kVarh]"}
    }),

    // Converte i valori in numeri
    ConvertToNumbers = Table.TransformColumnTypes(RenamedColumns, {
        {"EE [kWh]", type number},
        {"Q [kVarh]", type number}
    })
in
    ConvertToNumbers
