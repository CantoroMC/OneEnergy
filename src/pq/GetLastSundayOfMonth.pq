(year as number, month as number) as date =>
    let
        lastDay = Date.EndOfMonth(#date(year, month, 1)),
        daysToSubtract = Date.DayOfWeek(lastDay, Day.Sunday),
        lastSunday = Date.AddDays(lastDay, -daysToSubtract)
    in 
        lastSunday