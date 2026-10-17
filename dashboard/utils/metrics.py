"""delay calculations shared by the dashboard charts"""

import pandas as pd


def delay_summary(completed: pd.DataFrame, group_by: list[str]) -> pd.DataFrame:
    """
    Per group: completed flights, delayed flights and share delayed (0 to 1).

    Expects only completed flights, since onley they can be on time or delayed.
    """
    summary = (
        completed.groupby(group_by)
        .agg(flights=("is_delayed", "size"), delayed=("is_delayed", "sum"))
        .reset_index()
    )

    summary["delay_share"] = summary["delayed"] / summary["flights"]
    return summary
