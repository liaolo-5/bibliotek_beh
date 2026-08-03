import streamlit as st
from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

st.title("📚 BEH Bibliotek")
test = supabase.table("books").select("*").execute()


if "success_message" in st.session_state:
    st.success(st.session_state["success_message"])
    del st.session_state["success_message"]


def get_bibliotek():

    response = supabase.table("books") \
        .select("*") \
        .order("titel") \
        .execute()

    bibliotek = {}

    for row in response.data:
        bibliotek[row["id"]] = {
            "titel": row["titel"],
            "författare": row["forfattare"],
            "antal": row["antal"],
            "tillgängliga": row["tillgangliga"],
            "låntagare": row["lantagare"].split(",") if row["lantagare"] else []
        }

    return bibliotek

bibliotek = get_bibliotek()


def sorted_books(bibliotek):
    return sorted(bibliotek.items(), key=lambda x: x[1]["titel"])




# --- SÖK ---
sok = st.text_input("🔍 Sök bok (titel eller författare)").lower().strip()

result = []
st.subheader("📖 Böcker i biblioteket")

for book_id, data in sorted_books(bibliotek):
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
            input_key = f"name_{book_id}"
        
            # init state
            if input_key not in st.session_state:
                st.session_state[input_key] = ""
        
            # RESET-logik (viktigt)
            if st.session_state.get(f"reset_{book_id}", False):
                st.session_state[input_key] = ""
                st.session_state[f"reset_{book_id}"] = False
        
            namn = st.text_input("Namn", key=input_key)
        
            if f"msg_{book_id}" in st.session_state:
                st.success(st.session_state[f"msg_{book_id}"])
                del st.session_state[f"msg_{book_id}"]
                
        #LÅNA BOK
            if st.button("Låna", key=f"loan_{book_id}"):
        
                namn_clean = st.session_state.get(input_key, "").strip()
        
                if namn_clean == "":
                    st.warning("⚠️ Skriv namn först")
        
                elif data["tillgängliga"] <= 0:
                    st.error("❌ Boken är slut")
        
                else:
                    data["tillgängliga"] -= 1
                    data["låntagare"].append(namn_clean.title())
        
                    supabase.table("books").update({
                        "tillgangliga": data["tillgängliga"],
                        "lantagare": ",".join(data["låntagare"])
                    }).eq("id", book_id).execute()
        
                    st.session_state[f"msg_{book_id}"] = (
                        f"✅ {namn_clean.title()} lånade {data['titel']}"
                    )
        
                    # 🔥 istället för att skriva direkt till input
                    st.session_state[f"reset_{book_id}"] = True
        
                    st.rerun()

st.sidebar.header("🔁 Returnera bok")
if "return_msg" in st.session_state:
    st.sidebar.success(st.session_state["return_msg"])
    del st.session_state["return_msg"]

# lista bara böcker som har låntagare
valbara_bocker = [
    f"{bid} - {data['titel']}"
    for bid, data in sorted_books(bibliotek)
    if len(data["låntagare"]) > 0
]

val_bok = st.sidebar.selectbox("Välj bok", valbara_bocker)


if val_bok:
    book_id = val_bok.split(" - ")[0]
    data = get_bibliotek()[book_id]

    namn = st.sidebar.selectbox(
        "Vem ska returnera?",
        data["låntagare"],
        key="return_name"
    )

    if st.sidebar.button("Returnera", key="return_btn"):
        data["låntagare"].remove(namn)
        data["tillgängliga"] += 1

        cursor.execute("""
        UPDATE books
        SET tillgangliga = ?,
            lantagare = ?
        WHERE id = ?
        """, (
            data["tillgängliga"],
            ",".join(data["låntagare"]),
            book_id
        ))

        conn.commit()

        st.session_state["return_msg"] = f"🔁 {namn} returnerade '{data['titel']}'"
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
    
        if not titel:
            st.sidebar.error("Titel saknas")
    
        elif not författare:
            st.sidebar.error("Författare saknas")
    
        else:
            response = supabase.table("books") \
                .select("id") \
                .execute()
            
            ids = [row["id"] for row in response.data]
            
            if ids:
                last_number = max(
                    int(book_id[1:]) for book_id in ids
                )
                next_id = last_number + 1
            else:
                next_id = 1
    
            book_id = f"B{next_id}"
    
            supabase.table("books").insert({
                "id": book_id,
                "titel": titel,
                "forfattare": författare,
                "antal": int(antal),
                "tillgangliga": int(antal),
                "lantagare": ""
            }).execute()
    
            st.sidebar.success(f"Bok tillagd: {titel}")
            st.rerun()

    st.sidebar.subheader("❌ Ta bort bok")

        # --- steg 1: välj bok ---
    remove_choice = st.sidebar.selectbox(
        "Välj bok att ta bort",
        [f"{bid} - {data['titel']}" for bid, data in sorted_books(bibliotek)],
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
                cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
                conn.commit()
            
                st.session_state["success_message"] = f"{titel} borttagen"
                st.session_state.pop("confirm_delete", None)
            
                st.rerun()

        with col2:
            if st.button("Avbryt", key="cancel_delete_btn"):
                st.sidebar.info("Avbrutet")

                del st.session_state["confirm_delete"]
                st.rerun()

    st.sidebar.subheader("✏️ Editera bok")

    edit_choice = st.sidebar.selectbox(
        "Välj bok att editera",
        [f"{bid} - {data['titel']}" for bid, data in sorted_books(get_bibliotek())],
    )
    
    if edit_choice:
        book_id = edit_choice.split(" - ")[0]
        book = get_bibliotek()[book_id]

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
        
            nytt_tillgangligt = max(
                0,
                int(book["tillgängliga"]) + skillnad
            )
        
            cursor.execute("""
            UPDATE books
            SET titel = ?,
                forfattare = ?,
                antal = ?,
                tillgangliga = ?
            WHERE id = ?
            """, (
                ny_titel,
                ny_forfattare,
                int(nytt_antal),
                nytt_tillgangligt,
                book_id
            ))
        
            conn.commit()
        
            st.sidebar.success("Boken uppdaterad!")
            st.rerun()

