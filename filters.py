def money_filter(value):
  if value < 0:
    return "-${:,.2f}".format(float(abs(value)))
  return "${:,.2f}".format(float(value))

def format_date_spanish(date, short=False):
  months = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
  }
  
  day = date.day
  month = months[date.month]
  year = date.year
  
  if short:
    return f"{month.capitalize()} de {year}"
  
  return f"{day} de {month} de {year}"