import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# 1. LOAD DATA MENTAH
df = pd.read_csv("konsumsibbm.csv")

# Ambil kolom yang dipakai
df = df[['distance', 'consume', 'speed', 'temp_inside', 'temp_outside' ]]

# 2. CLEANING DATA
for col in ['distance', 'consume', 'temp_inside', 'temp_outside']:
    df[col] = df[col].astype(str).str.replace(',', '.')

df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
df['consume'] = pd.to_numeric(df['consume'], errors='coerce')
df['speed'] = pd.to_numeric(df['speed'], errors='coerce')
df['temp_inside'] = pd.to_numeric(df['temp_inside'], errors='coerce')
df['temp_outside'] = pd.to_numeric(df['temp_outside'], errors='coerce')

# Hapus data kosong
df = df.dropna()

# 3. SIMPAN DATA BERSIH
df.to_csv("data_bersih.csv", index=False)

print("Data bersih berhasil disimpan\n")

# 4. LOAD DATA BERSIH
df_bersih = pd.read_csv("data_bersih.csv")

# 5. SIAPKAN DATA
X = df_bersih[['distance', 'speed', 'temp_inside', 'temp_outside']]
y = df_bersih['consume']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# 6. TRAIN MODEL

model = LinearRegression()
model.fit(X_train, y_train)

print("Model berhasil dilatih!")


# 7. EVALUASI MODEL

y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)

print(f"Akurasi model (R2 Score): {r2:.4f}")


# 8. INPUT USER
jarak = float(input("Masukkan jarak (km): "))
kecepatan = float(input("Masukkan kecepatan (km/h): "))
suhu_inside = float(input("Masukan suhu inside : "))
suhu_outside = float(input("Masukan suhu outside : "))

suhu_inside = (suhu_inside * 9/5) +32
suhu_outside = (suhu_outside * 9/5) +32

# 9. PREDIKSI
input_data = pd.DataFrame(
    [[jarak, kecepatan, suhu_inside, suhu_outside]],
    columns=['distance', 'speed','temp_inside', 'temp_outside']
)

prediksi = model.predict(input_data)


# 10. OUTPUT

print("\n HASIL PREDIKSI ")
print(f"Jarak       : {jarak} km")
print(f"Kecepatan   : {kecepatan} km/h")
print(f"Suhu inside: {suhu_inside} °C")
print(f"Suhu outside: {suhu_outside} °C")
print(f"Konsumsi BBM: {prediksi[0]:.2f} liter")