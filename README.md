# Uruchomienie projektu

Wymagany jest Python 3.10 lub nowszy. Otwórz trzy osobne okna PowerShell lub CMD i w
każdym przejdź do katalogu projektu:

---powershell
Set-Location C:\ścieżka\do\projektu

---cmd
cd C:\ścieżka\do\projektu


W pierwszym oknie uruchom Serwis Produktów:

---powershell lub cmd
python product_service.py


W drugim oknie uruchom Serwis Magazynowy:

---powershell lub cmd
python stock_service.py


Pozostaw oba serwisy uruchomione. Nasłuchują odpowiednio na portach 8001 i
8002. 

Trzeciego okna użyj do wysłania żądań:

---powershell lub cmd
curl.exe -i http://127.0.0.1:8002/stock/123
curl.exe -i http://127.0.0.1:8002/stock/999