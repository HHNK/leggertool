# %%
from math import sqrt
import sqlite3
import pandas as pd

path = r"C:\Users\wvanesse\Desktop\schermer_error_varianten.gpkg"

def calc_pitlo_griffioen(flow, ditch_bottom_width, water_depth, slope, friction_manning, friction_begroeiing,
                         begroeiingsdeel):
    """
    A calculation of the formula for gradient in the water level according to Pitlo and Griffioen.
    Based on physical parameters like normative flow, ditch width, water depth and plant growth within the profile.
    """
    flow = abs(flow)
    water_depth = float(water_depth)
    ditch_bottom_width = float(ditch_bottom_width)
    slope = float(slope)

    width_at_waterlevel = ditch_bottom_width + 2 * water_depth * slope

    ditch_circumference = width_at_waterlevel + 2 * (1 - begroeiingsdeel) * water_depth

    total_cross_section_area = 0.5 * (
            width_at_waterlevel - ditch_bottom_width) * water_depth + ditch_bottom_width * water_depth

    A_1 = (1 - begroeiingsdeel) * total_cross_section_area
    A_2 = begroeiingsdeel * total_cross_section_area
    R = A_1 / ditch_circumference
    B = A_2 * friction_begroeiing
    C = friction_manning * A_1 * (R ** 0.66666666666667)

    if B == 0:
        gradient = 99999999
    else:

        try:
            gradient = 100000 * (2 * B * flow + C ** 2 - C * sqrt(4 * B * flow + C ** 2)) / (2 * B ** 2)
        except TypeError:
            gradient = 99999

    return gradient
# %%

with sqlite3.connect(path) as conn:
    # varianten = pd.read_sql("SELECT * FROM varianten;", conn)
    hydro_objects_kenmerken = pd.read_sql("SELECT * FROM hydroobjects_selected_legger;", conn)
    begroeiingsvariants = pd.read_sql("""Select  id, naam, friction_manning, friction_begroeiing, begroeiingsdeel from begroeiingsvariant ORDER BY begroeiingsdeel""", conn)

# alles = hydro_objects_kenmerken.merge(varianten,how="left",left_on="id",right_on="")

# %%
varhang = []
for index,variant in hydro_objects_kenmerken.iterrows():

    # variant_id = variant['id']
    debiet = abs(variant['debiet'])
    debiet_inlaat = variant['debiet_inlaat']
    # peil_diff_inlaat = variant['peil_diff_inlaat']
    hydraulische_talud = variant['geselecteerd_talud']
    hydraulische_bodembreedte = variant['geselecteerde_hydraulische_bodembreedte']
    hydraulische_diepte = variant['geselecteerde_hydraulische_diepte']
    begroeiingsvariant_id = variant['geselecteerde_begroeiingsvariant']

    friction_manning = begroeiingsvariants[begroeiingsvariants["id"] == begroeiingsvariant_id]['friction_manning'].to_numpy()
    friction_begroeiing = begroeiingsvariants[begroeiingsvariants["id"] == begroeiingsvariant_id]['friction_begroeiing'].to_numpy()
    begroeiingsdeel = begroeiingsvariants[begroeiingsvariants["id"] == begroeiingsvariant_id]['begroeiingsdeel'].to_numpy()

    verhang = calc_pitlo_griffioen(
        flow=debiet,
        ditch_bottom_width=hydraulische_bodembreedte,
        water_depth=hydraulische_diepte,
        slope=hydraulische_talud,
        friction_manning= friction_manning,
        friction_begroeiing=friction_begroeiing,
        begroeiingsdeel=begroeiingsdeel
    )
    # verhang_inlaat = calc_pitlo_griffioen(
    #     flow=debiet_inlaat,
    #     ditch_bottom_width=hydraulische_bodembreedte,
    #     water_depth=hydraulische_diepte + peil_diff_inlaat,
    #     slope=hydraulische_talud,
    #     friction_manning=friction_manning,
    #     friction_begroeiing=friction_begroeiing,
    #     begroeiingsdeel=begroeiingsdeel
    #     )
# %%
