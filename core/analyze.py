import pandas as pd

def mergeCSV(result, ai1, ai2, ai3):
    '''get all csv's make a new csv with plate columns and file names come from results.csv
    '''
    results = pd.read_csv(result)
    df1 = pd.read_csv(ai1)
    df2 = pd.read_csv(ai2)
    df3 = pd.read_csv(ai3)

    df1 = df1.add_suffix("_ai1").rename(columns={"filename_ai1": "filename"})
    df2 = df2.add_suffix("_ai2").rename(columns={"filename_ai2": "filename"})
    df3 = df3.add_suffix("_ai3").rename(columns={"filename_ai3": "filename"})

    df = pd.merge(df1, df2, on="filename")
    df = pd.merge(df, df3, on="filename")
    df = pd.merge(df, results, on="filename", how="left")

    analyze(df)


def analyze(df):

    df["all_agree"] = (df["plate_ai1"] == df["plate_ai2"]) & (df["plate_ai2"] == df["plate_ai3"])

    df["bucket"] = df.apply(bucket, axis=1) #calls bucked() for each row

    df.to_csv("results_merged.csv", index=False)



def bucket(row):
    if row["plate_ai1"] == row["plate_ai2"] == row["plate_ai3"]:
        if row["plate_ai1"] == row["alpr_plate"]:
            return "agreed"
        else:
            return "disagreed"
    else:
        return "manual"


    