// Example Power Query M script to read Parquet files in Power BI
// Replace existing CSV imports with these Parquet readers

// ============================================
// PUN - Energy Prices (from Parquet)
// ============================================
let
    // Read the Parquet file
    Source = Parquet.Document(File.Contents("C:\Users\marco\Documents\Home\03_LIABILITIES\Utilities\Energia\Management\db\OneEnergy\db\PUN-MGP.parquet")),

    // The data is already optimized with correct types
    // Date is datetime, Hour is int8, PUN is float32

    // Optional: Add DateTime column combining Date and Hour
    AddDateTime = Table.AddColumn(Source, "DateTime", each
        DateTime.From([Date]) + #duration(0, [Hour]-1, 0, 0),
        type datetime
    ),

    // Optional: Sort by DateTime
    SortedRows = Table.Sort(AddDateTime, {{"DateTime", Order.Ascending}})
in
    SortedRows

// ============================================
// Consumi - Consumption Data (from Parquet)
// ============================================
let
    // Option 1: Read single file (all data)
    Source = Parquet.Document(File.Contents("C:\Users\marco\Documents\Home\03_LIABILITIES\Utilities\Energia\Management\db\OneEnergy\db\IT012E00801406.parquet")),

    // Option 2: Read partitioned data (if you want specific years)
    // Source = Folder.Files("C:\Users\marco\Documents\Home\03_LIABILITIES\Utilities\Energia\Management\db\OneEnergy\db\Consumi"),
    // FilterParquet = Table.SelectRows(Source, each [Extension] = ".parquet"),
    // CombineFiles = Table.Combine(Table.TransformColumns(FilterParquet, {"Content", each Parquet.Document(_)})),

    // Select relevant columns
    SelectColumns = Table.SelectColumns(Source, {
        "DateTime",
        "POD",
        "FL_ORA_LEGALE",
        "CONSUMO_ATTIVA_PRELEVATA",
        "ATTIVA_IMMESSA",
        "CONSUMO_PICCO_PRELEVATA"
    }),

    // Rename for clarity if needed
    RenamedColumns = Table.RenameColumns(SelectColumns, {
        {"CONSUMO_ATTIVA_PRELEVATA", "ConsumoAttivo"},
        {"ATTIVA_IMMESSA", "Immessa"},
        {"FL_ORA_LEGALE", "OraLegale"}
    })
in
    RenamedColumns

// ============================================
// Performance Tips for Parquet in Power BI
// ============================================
/*
1. DIRECT QUERY: Parquet files don't support DirectQuery mode
   - Use Import mode for best performance
   - Enable incremental refresh if data grows

2. FOLDER CONNECTOR: For multiple Parquet files
   let
       Source = Folder.Files("path\to\folder"),
       ParquetFiles = Table.SelectRows(Source, each [Extension] = ".parquet"),
       CombineFiles = Table.Combine(
           Table.TransformColumns(ParquetFiles, {
               "Content", each Parquet.Document(_)
           })[Content]
       )
   in
       CombineFiles

3. FILTER EARLY: Apply filters before loading
   let
       Source = Parquet.Document(File.Contents("path\to\file.parquet")),
       FilteredRows = Table.SelectRows(Source, each [Date] >= #date(2024, 1, 1))
   in
       FilteredRows

4. COLUMN SELECTION: Only load needed columns
   - Parquet reads only selected columns (columnar format benefit)

5. DATA TYPES: Already optimized in Parquet
   - No need to change types (already done in conversion)
   - int8 for hours, float32 for values saves memory

6. PARTITIONING: Use Year partitions for large datasets
   - Query specific years directly from folders
   - Reduces data scanning

7. REFRESH STRATEGY:
   - Keep last 2 years in memory
   - Archive older data with aggregations
*/

// ============================================
// Join PUN and Consumi Example
// ============================================
let
    // Load PUN prices
    PUN = Parquet.Document(File.Contents("C:\...\db\PUN-MGP.parquet")),
    PUNWithDateTime = Table.AddColumn(PUN, "DateTime", each
        DateTime.From([Date]) + #duration(0, [Hour]-1, 0, 0),
        type datetime
    ),

    // Load Consumption
    Consumi = Parquet.Document(File.Contents("C:\...\db\IT012E00801406.parquet")),

    // Extract hour from consumption DateTime for joining
    ConsumiWithHour = Table.AddColumn(Consumi, "Hour", each
        Time.Hour([DateTime]) + 1,  // PUN uses 1-24, not 0-23
        Int64.Type
    ),
    ConsumiWithDate = Table.AddColumn(ConsumiWithHour, "Date", each
        Date.From([DateTime]),
        type date
    ),

    // Join on Date and Hour
    Joined = Table.NestedJoin(
        ConsumiWithDate, {"Date", "Hour"},
        PUN, {"Date", "Hour"},
        "PriceData", JoinKind.LeftOuter
    ),

    // Expand price data
    ExpandedPrice = Table.ExpandTableColumn(Joined, "PriceData", {"PUN"}, {"PUN"}),

    // Calculate cost
    WithCost = Table.AddColumn(ExpandedPrice, "Cost", each
        [CONSUMO_ATTIVA_PRELEVATA] * [PUN] / 1000,  // kWh * EUR/MWh
        type number
    )
in
    WithCost