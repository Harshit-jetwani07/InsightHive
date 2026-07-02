from services.sample_data import build_retail_demo_dataset


def test_demo_dataset_has_strong_business_dimensions():
    df = build_retail_demo_dataset()
    required = {
        "Parsed_Date",
        "Region",
        "Product",
        "Revenue",
        "Revenue_Target",
        "Profit",
        "Profit_Margin",
        "Return_Rate",
        "Target_Achieved",
    }
    assert required.issubset(df.columns)
    assert len(df) >= 1500
    assert df["Region"].nunique() == 4
    assert df["Product"].nunique() == 4


def test_demo_dataset_contains_explainable_risk_signal():
    df = build_retail_demo_dataset()
    south_apparel = df[(df["Region"] == "South") & (df["Product"] == "Apparel")]
    other = df[~((df["Region"] == "South") & (df["Product"] == "Apparel"))]
    assert south_apparel["Return_Rate"].mean() > other["Return_Rate"].mean()
