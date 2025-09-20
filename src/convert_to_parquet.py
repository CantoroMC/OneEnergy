"""
Convert CSV energy data files to Parquet format for improved performance.
Optimizes data types and applies compression for faster Power BI loading.
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import sys
from datetime import datetime

def convert_pun_mgp(db_path):
    """Convert PUN-MGP price data to Parquet."""
    print("Converting PUN-MGP.csv...")

    # Read CSV with correct separator
    df = pd.read_csv(db_path / 'PUN-MGP.csv', sep=';', encoding='utf-8-sig')

    # Parse date (format: YYYYMMDD)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

    # Optimize data types
    df['Hour'] = df['Hour'].astype('int8')  # Hours 1-24 fit in int8
    df['PUN'] = df['PUN'].astype('float32')  # Price precision sufficient with float32

    # Add year column for potential partitioning
    df['Year'] = df['Date'].dt.year.astype('int16')

    # Save as Parquet with compression
    output_path = db_path / 'PUN-MGP.parquet'
    df.to_parquet(
        output_path,
        compression='snappy',  # Fast compression
        index=False,
        engine='pyarrow'
    )

    # Report statistics
    original_size = (db_path / 'PUN-MGP.csv').stat().st_size / 1024 / 1024
    new_size = output_path.stat().st_size / 1024 / 1024
    reduction = (1 - new_size/original_size) * 100

    print(f"  - Rows: {len(df):,}")
    print(f"  - Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    print(f"  - Size: {original_size:.2f} MB -> {new_size:.2f} MB ({reduction:.1f}% reduction)")

    return df

def convert_consumi(db_path):
    """Convert consumption data (IT012E00801406) to Parquet."""
    print("\nConverting IT012E00801406.csv (Consumi)...")

    # Read CSV
    df = pd.read_csv(db_path / 'IT012E00801406.csv', sep=';', encoding='utf-8')

    # Parse date and time (DATA: YYYYMMDD, ORA: HHMM00)
    df['DateTime'] = pd.to_datetime(
        df['DATA'].astype(str) + ' ' + df['ORA'].astype(str).str.zfill(6),
        format='%Y%m%d %H%M%S'
    )

    # Optimize data types
    numeric_columns = [
        'CONSUMO_ATTIVA_PRELEVATA',
        'ATTIVA_IMMESSA',
        'CONSUMO_REATTIVA_INDUTTIVA_PRELEVATA',
        'REATTIVA_INDUTTIVA_IMMESSA',
        'CONSUMO_REATTIVA_CAPACITIVA_PRELEVATA',
        'REATTIVA_CAPACITIVA_IMMESSA',
        'CONSUMO_PICCO_PRELEVATA',
        'CONSUMO_PICCO_IMMESSA'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')

    df['FL_ORA_LEGALE'] = df['FL_ORA_LEGALE'].astype('int8')

    # Add year and month for partitioning
    df['Year'] = df['DateTime'].dt.year.astype('int16')
    df['Month'] = df['DateTime'].dt.month.astype('int8')

    # Save as partitioned Parquet (by Year for better query performance)
    output_path = db_path / 'Consumi'

    # Create partitioned dataset
    table = pa.Table.from_pandas(df)
    pq.write_to_dataset(
        table,
        root_path=str(output_path),
        partition_cols=['Year'],
        compression='snappy'
    )

    # Also create single file version for simpler access
    single_file_path = db_path / 'IT012E00801406.parquet'
    df.to_parquet(
        single_file_path,
        compression='snappy',
        index=False,
        engine='pyarrow'
    )

    # Report statistics
    original_size = (db_path / 'IT012E00801406.csv').stat().st_size / 1024 / 1024
    new_size = single_file_path.stat().st_size / 1024 / 1024
    reduction = (1 - new_size/original_size) * 100

    print(f"  - Rows: {len(df):,}")
    print(f"  - Date range: {df['DateTime'].min()} to {df['DateTime'].max()}")
    print(f"  - 15-minute intervals captured")
    print(f"  - Size: {original_size:.2f} MB -> {new_size:.2f} MB ({reduction:.1f}% reduction)")
    print(f"  - Partitioned by Year in: {output_path}/")

    return df

def convert_gas_mgp(db_path):
    """Convert GAS-MGP data to Parquet."""
    print("\nConverting GAS-MGP.csv...")

    # Read CSV
    df = pd.read_csv(db_path / 'GAS-MGP.csv', sep=';', encoding='utf-8-sig')

    # Identify and parse date column (first column likely)
    date_col = df.columns[0]
    df['Date'] = pd.to_datetime(df[date_col], format='%Y%m%d', errors='coerce')

    # Convert numeric columns
    for col in df.columns:
        if col not in ['Date', date_col]:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')

    # Save as Parquet
    output_path = db_path / 'GAS-MGP.parquet'
    df.to_parquet(
        output_path,
        compression='snappy',
        index=False,
        engine='pyarrow'
    )

    original_size = (db_path / 'GAS-MGP.csv').stat().st_size / 1024
    new_size = output_path.stat().st_size / 1024

    print(f"  - Rows: {len(df):,}")
    print(f"  - Size: {original_size:.1f} KB -> {new_size:.1f} KB")

    return df

def main():
    """Main conversion function."""
    # Get database path
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'db'

    if not db_path.exists():
        print(f"Error: Database directory not found at {db_path}")
        sys.exit(1)

    print(f"Converting CSV files to Parquet format...")
    print(f"Database path: {db_path}\n")
    print("=" * 50)

    try:
        # Convert main data files
        pun_df = convert_pun_mgp(db_path)
        consumi_df = convert_consumi(db_path)

        # Convert smaller files if they exist
        if (db_path / 'GAS-MGP.csv').exists():
            gas_df = convert_gas_mgp(db_path)

        # Convert PSV files if they exist
        for psv_file in ['PSV_DA.csv', 'PSV_MA.csv']:
            if (db_path / psv_file).exists():
                print(f"\nConverting {psv_file}...")
                df = pd.read_csv(db_path / psv_file, sep=';', encoding='utf-8')
                output = db_path / psv_file.replace('.csv', '.parquet')
                df.to_parquet(output, compression='snappy', index=False)
                print(f"  - Converted to {output.name}")

        print("\n" + "=" * 50)
        print("Conversion completed successfully!")
        print("\nNext steps:")
        print("1. Update Power Query scripts to read .parquet files")
        print("2. Test Power BI performance with new format")
        print("3. Keep CSV files as backup until verified")

    except Exception as e:
        print(f"\nError during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()