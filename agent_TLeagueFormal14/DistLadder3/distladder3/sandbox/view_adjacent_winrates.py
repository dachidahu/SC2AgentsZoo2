fn_all = [
    "IL-model_20200824171223",
    "IL-model_20200824174547",
    "IL-model_20200824181523",
    "IL-model_20200824184505",
    "IL-model_20200824191503",
    "IL-model_20200824194508",
    "IL-model_20200824201508",
    "IL-model_20200824204514",
    "IL-model_20200824211519",
    "IL-model_20200824214525",
    "IL-model_20200824221532",
    "IL-model_20200824224540",
    "IL-model_20200824231548",
    "IL-model_20200824234558",
    "IL-model_20200825001609",
    "IL-model_20200825004620",
    "IL-model_20200825011630",
    "IL-model_20200825014639",
    "IL-model_20200825021650",
    "IL-model_20200825024659",
    "IL-model_20200825031710",
    "IL-model_20200825034720",
    "IL-model_20200825041727",
    "IL-model_20200825044738",
    "IL-model_20200825051748",
    "IL-model_20200825054758",
    "IL-model_20200825061809",
    "IL-model_20200825064820",
    "IL-model_20200825071831",
    "IL-model_20200825074845",
    "IL-model_20200825081858",
    "IL-model_20200825084911",
    "IL-model_20200825091923",
    "IL-model_20200825094934",
    "IL-model_20200825101946",
    "IL-model_20200825105000",
    "IL-model_20200825112014",
    "IL-model_20200825115027",
    "IL-model_20200825122040",
    "IL-model_20200825125049",
    "IL-model_20200825132102",
    "IL-model_20200825135116",
    "IL-model_20200825142127",
    "IL-model_20200825145141",
    "IL-model_20200825152154",
    "IL-model_20200825155210",
    "IL-model_20200825162221",
    "IL-model_20200825165235",
    "IL-model_20200825172247",
    "IL-model_20200825175303",
    "IL-model_20200825182316",
    "IL-model_20200825185331",
    "IL-model_20200825192345",
    "IL-model_20200825195357",
    "IL-model_20200825202413",
    "IL-model_20200825205424",
    "IL-model_20200825212438",
    "IL-model_20200825215452",
    "IL-model_20200825222504",
    "IL-model_20200825225521",
    "IL-model_20200825232533",
    "IL-model_20200825235544",
    "IL-model_20200826002559",
    "IL-model_20200826005611",
    "IL-model_20200826012623",
    "IL-model_20200826015636",
    "IL-model_20200826022645",
    "IL-model_20200826025658",
    "IL-model_20200826032710",
    "IL-model_20200826035723",
]

fn2 = [
    "IL-model_20200824211519",
    "IL-model_20200825011630",
    "IL-model_20200825031710",
    "IL-model_20200825112014",
    "IL-model_20200825132102",
    "IL-model_20200825152154",
    "IL-model_20200825192345",
]

for f in fn2:
  idx = fn_all.index(f)
  print(fn_all[idx-1])
  print(fn_all[idx])
  print(fn_all[idx+1])

