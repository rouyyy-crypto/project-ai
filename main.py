import gradio as gr


def make_greeting(name: str, excited: bool) -> str:
    greeting = f"Hello, {name}!"
    if excited:
            greeting = greeting.upper() + "!!!"
    return greeting


demo = gr.Interface(
    fn=make_greeting,  
    inputs=[  
        gr.Textbox(label="Name"),
        gr.Checkbox(label="Excited")
    ],
    outputs=gr.Textbox(label="Greeting"),  
    title="The Greeting Application",
    submit_btn="Greet",
    flagging_mode="never"  
)


demo.launch()