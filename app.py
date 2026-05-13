import streamlit as st
import json
import os

ADMIN_PASSWORD = "211"

st.title("📚 BEH Bibliotek")


# --- DATA (din struktur) ---
def load_data():
    if os.path.exists("bibliotek.json"):
        with open("bibliotek.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


bibliotek = load_data()


def sorted_books():
    return sorted(bibliotek.items(), key=lambda x: x[1]["titel"].lower())


def save_data():
    with open("bibliotek.json", "w", encoding="utf-8") as f:
        json.dump(bibliotek, f, ensure_ascii=False, indent=4)


# --- SÖK ---
sok = st.text_input("🔍 Sök bok (titel eller författare)").lower().strip()

result = []
st.subheader("📖 Böcker i biblioteket")

for book_id, data in sorted_books():
    titel = str(data.get("titel", "")).lower()
    forfattare = str(data.get("författare", "")).lower()

    if sok and (sok not in titel and sok not in forfattare):
        continue

    with st.container():
        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(f"📘 {data['titel']}")
            st.write(f"✍️ {data['författare']}")
            st.write(f"📦 Tillgängliga: {data['tillgängliga']}")

        with col2:
            namn = st.text_input("Namn", key=input_key)

            if st.button("Låna", key=f"loan_{book_id}"):

                if namn.strip() == "":
                    st.warning("⚠️ Skriv namn först")
            
                elif data["tillgängliga"] <= 0:
                    st.error("❌ Boken är slut")
            
                else:
                    data["tillgängliga"] -= 1
                    data["låntagare"].append(namn.strip().title())
            
                    save_data()
            
                    st.success(f"✅ {namn} lånade {data['titel']}")
            
                    # töm inputfältet
                    st.session_state[input_key] = ""
            
                    st.rerun()

st.sidebar.header("🔁 Returnera bok")

# lista bara böcker som har låntagare
valbara_bocker = [
    f"{bid} - {data['titel']}"
    for bid, data in sorted_books()
    if len(data["låntagare"]) > 0
]

val_bok = st.sidebar.selectbox("Välj bok", valbara_bocker)

if val_bok:
    book_id = val_bok.split(" - ")[0]
    data = bibliotek[book_id]

    namn = st.sidebar.selectbox("Vem ska returnera?", data["låntagare"], key="return_name")

    if st.sidebar.button("Returnera", key="return_btn"):
        data["låntagare"].remove(namn)
        data["tillgängliga"] += 1

        st.sidebar.success(f"{namn} returnerade {data['titel']}")
        save_data()
        st.rerun()

st.sidebar.header("🔐 Admin")

password = st.sidebar.text_input("Lösenord", type="password")

if password == ADMIN_PASSWORD:
    st.sidebar.success("Åtkomst beviljad")

    st.sidebar.subheader("➕ Lägg till bok")

    titel = st.sidebar.text_input("Titel").title().strip()
    författare = st.sidebar.text_input("Författare").title().strip()
    antal = st.sidebar.number_input("Antal", min_value=1, step=1)

    if st.sidebar.button("Lägg till bok"):
        book_id = f"B{len(bibliotek) + 1}"

        bibliotek[book_id] = {
            "titel": titel,
            "författare": författare,
            "antal": int(antal),
            "tillgängliga": int(antal),
            "låntagare": [],
        }

        st.sidebar.success(f"Bok tillagd: {titel}")
        save_data()
        st.rerun()

    st.sidebar.subheader("❌ Ta bort bok")

        # --- steg 1: välj bok ---
    remove_choice = st.sidebar.selectbox(
        "Välj bok att ta bort",
        [f"{bid} - {data['titel']}" for bid, data in sorted_books()],
        key="remove_select"
    )
    
    if remove_choice:
        book_id = remove_choice.split(" - ")[0]
        titel = bibliotek[book_id]["titel"]
    
        # --- klicka initiera delete ---
        if st.sidebar.button("🗑 Ta bort bok", key="delete_btn"):
            st.session_state["confirm_delete"] = book_id
    
    # --- steg 2: bekräftelse ---
    if "confirm_delete" in st.session_state:
        book_id = st.session_state["confirm_delete"]
        titel = bibliotek[book_id]["titel"]
    
        st.sidebar.warning(f"Är du säker på att du vill ta bort '{titel}'?")
    
        col1, col2 = st.sidebar.columns(2)
    
        with col1:
            if st.button("Ja, ta bort", key="confirm_delete_btn"):
                del bibliotek[book_id]
                save_data()
                st.sidebar.success(f"{titel} borttagen")
    
                del st.session_state["confirm_delete"]
                st.rerun()

        with col2:
            if st.button("Avbryt", key="cancel_delete_btn"):
                st.sidebar.info("Avbrutet")

                del st.session_state["confirm_delete"]
                st.rerun()

    st.sidebar.subheader("✏️ Editera bok")

    edit_choice = st.sidebar.selectbox(
        "Välj bok att editera",
        [f"{bid} - {data['titel']}" for bid, data in sorted_books()],
        key="edit_select",
    )

    if edit_choice:
        book_id = edit_choice.split(" - ")[0]
        book = bibliotek[book_id]

        ny_titel = st.sidebar.text_input(
            "Titel", value=str(book.get("titel", "")), key=f"title_{book_id}"
        )

        ny_forfattare = st.sidebar.text_input(
            "Författare", value=str(book.get("författare", "")), key=f"author_{book_id}"
        )

        nytt_antal = st.sidebar.number_input(
            "Antal",
            min_value=1,
            value=int(book.get("antal", 1)),
            key=f"antal_{book_id}",
        )

        if st.sidebar.button("Spara ändringar"):
            skillnad = int(nytt_antal) - int(book["antal"])

            book["titel"] = ny_titel
            book["författare"] = ny_forfattare
            book["antal"] = int(nytt_antal)
            book["tillgängliga"] += skillnad

            st.sidebar.success("Boken uppdaterad!")
            save_data()
            st.rerun()
