use crate::{chat::ChatMessage, AppMessage};
use hello_egui::inbox::UiInboxSender;

pub struct SharedState {
    pub tx: UiInboxSender<AppMessage>,
    pub active_route: String,
}

impl SharedState {
    pub fn new(tx: UiInboxSender<AppMessage>) -> Self {
        Self {
            tx,
            active_route: "/example".to_string(),
        }

    }
}