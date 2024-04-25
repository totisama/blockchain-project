import streamlit as st
import requests


# Data for the proposals

proposals = [
    {"title": "Best Fast Food After Clubbing", "description": "Vote for the best fast food restaurant.", "status": "active", "options": ["McDonald's", "Burger King", "KFC", "Wendy's"]},
    {"title": "Best K-Pop Group in 2024", "description": "Choose your favorite K-pop group.", "status": "closed", "options": ["BTS", "Blackpink", "EXO", "Twice"]},
    {"title": "Programming Language", "description": "What is the best programming language?", "status": "active", "options": ["Python", "JavaScript", "Java", "C#"]},
    {"title": "Favorite Superhero", "description": "Who is your favorite superhero?", "status": "active", "options": ["Spider-Man", "Batman", "Superman", "Wonder Woman"]},
    {"title": "Best Streaming Service", "description": "Vote for your preferred streaming service.", "status": "active", "options": ["Netflix", "Hulu", "Amazon Prime", "Disney+"]},
    {"title": "Best Coffee Chain For Mondays", "description": "Choose the best coffee chain.", "status": "closed", "options": ["Starbucks", "Dunkin'", "Peet's Coffee", "Tim Hortons"]},
    {"title": "Top Vacation Destination", "description": "What's your top vacation destination?", "status": "active", "options": ["Hawaii", "Bali", "Paris", "Tokyo"]},
    {"title": "Best Smartphone Brand", "description": "Which is the best smartphone brand?", "status": "active", "options": ["Apple", "Samsung", "Google", "Huawei"]},
    {"title": "Favorite Book Genre", "description": "What is your favorite book genre?", "status": "closed", "options": ["Fantasy", "Science Fiction", "Mystery", "Romance"]},
    {"title": "Best Pet to Have in Spain", "description": "What is the best pet to have?", "status": "active", "options": ["Dog", "Cat", "Bird", "Fish"]},
    {"title": "Best Game Console", "description": "Vote for the best game console.", "status": "active", "options": ["PlayStation", "Xbox", "Nintendo Switch", "PC"]},
    {"title": "Favorite Type of Music", "description": "What's your favorite type of music?", "status": "closed", "options": ["Rock", "Pop", "Classical", "Jazz"]},
    {"title": "Best Fast Casual Restaurant", "description": "Choose the best fast casual restaurant.", "status": "active", "options": ["Chipotle", "Panera Bread", "Shake Shack", "Five Guys"]},
    {"title": "Best Car Brand (besides BMW)", "description": "What is the best car brand in your opinion?", "status": "active", "options": ["Toyota", "Ford", "BMW", "Tesla"]},
    {"title": "Top Fitness Activity", "description": "What's your top fitness activity?", "status": "active", "options": ["Yoga", "Running", "Gym", "Cycling"]},
    {"title": "Best Type of Vacation", "description": "What is the best type of vacation?", "status": "closed", "options": ["Beach", "Mountain", "City", "Cruise"]},
    {"title": "Favorite Ice Cream Flavor", "description": "What is your favorite ice cream flavor?", "status": "active", "options": ["Vanilla", "Chocolate", "Strawberry", "Mint Chocolate Chip"]},
    {"title": "Best Movie Genre in 21th Century", "description": "Vote for the best movie genre in our.", "status": "active", "options": ["Action", "Comedy", "Drama", "Horror"]},
    {"title": "Best Sleeping Position", "description": "What is your favourite position for a nice nap?", "status": "active", "options": ["On the side", "On the back", "On the other side", "On the stomach"]},
    {"title": "Best Colour from the Rainbow", "description": "Choose your favourite colour from the rainbow.", "status": "active", "options": ["Coca-Cola", "Pepsi", "Sprite", "Dr Pepper"]}
]
# Home page

def create_transaction():
    data = requests.get("http://127.0.0.1:8000/get-peers").json()
    print(data)

def home_page():
    st.title("Proposals")


    st.write("""
        # Test app
    """)

    st.button("Create transaction", on_click=create_transaction)


    num_columns = 3
    num_proposals = len(proposals)
    num_rows = (num_proposals + num_columns - 1) // num_columns

    rows = [st.columns(num_columns) for _ in range(num_rows)]

    for index, proposal in enumerate(proposals):
        row_index = index // num_columns
        col_index = index % num_columns
        col = rows[row_index][col_index]

        with col:
            with st.container(border=True, height=240):
                if proposal["status"] == "active":
                   st.caption(":green[Active]")
                else:
                    st.caption(":red[Closed]")

                st.markdown(f"<h4 style='margin-top:-20px;'>{proposal['title']}</h2>", unsafe_allow_html=True)
                st.markdown(proposal["description"])

                st.button("Vote", key=proposal["title"], on_click=load_proposal_page, args=(proposal,), type="primary", use_container_width=True)



# Proposal page

def load_proposal_page(proposal):
    st.session_state.current_proposal = proposal
    st.session_state.page = "Proposal"
    st.rerun()



# Proposal detail and voting form

def proposal_page():
    proposal = st.session_state.current_proposal
    if st.button("Back"):
        st.session_state.current_proposal = None
        st.session_state.page = "Home"
        st.rerun()
    if proposal["status"] == "active":
        st.caption(":green[Active]")
    else:
        st.caption(":red[Closed]")
    st.markdown(f"<h2 style='margin-top:-30px;'>{proposal['title']}</h2>", unsafe_allow_html=True)
    st.markdown(proposal["description"])

    if proposal["status"] == "active":
        vote = st.radio("Choose your option", proposal["options"])
        if st.button("Vote", type="primary"):
            send_vote(str(proposal['title']).replace(" ", ""),vote)
    else:
        st.error("Voting is over, sorry")

    if "results" in proposal:
        st.subheader("Voting Results")
        for option, count in proposal["results"].items():
            st.write(f"{option}: {count}%")



# Replace it with something real, now its just simulation of the voting

def send_vote(topic,vote):
    request = requests.get(f"http://127.0.0.1:8000/vote/{topic}/{vote}").json()
    print(request["response"])
    # results = {option: 0 for option in st.session_state.current_proposal["options"]}
    # results[vote] += 100
    # st.session_state.current_proposal["results"] = results
    # st.rerun()



# App function to control page rendering

def main():
    if "page" not in st.session_state:
        st.session_state.page = "Home"

    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Proposal":
        proposal_page()

if __name__ == "__main__":
    main()

