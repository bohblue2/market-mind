use crate::chat::CHAT_EXAMPLE;
use crate::shared_state::SharedState;
use egui::Ui;

pub const EXAMPLES: &[Category] = &[
    Category {
        name: "Q&A Chatbot",
        examples: &[CHAT_EXAMPLE],
    },
];

pub trait ExampleTrait {
    fn ui(&mut self, ui: &mut Ui, shared_state: &mut SharedState);
}

pub struct Category {
    pub name: &'static str,
    pub examples: &'static [Example],
}

pub struct Example {
    pub name: &'static str,
    pub slug: &'static str,
    pub get: fn() -> Box<dyn ExampleTrait>,
}

impl Example {
    pub fn get(&self) -> Box<dyn ExampleTrait> {
        (self.get)()
    }
}
