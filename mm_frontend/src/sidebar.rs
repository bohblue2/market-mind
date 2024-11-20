use crate::example::EXAMPLES;
use crate::shared_state::SharedState;
use crate::AppMessage;
use egui::{Align, Button, Layout, RichText, Ui, Vec2};
use hello_egui::flex::{Flex, FlexItem};

pub struct SideBar {}

impl SideBar {
    pub fn ui(ui: &mut Ui, shared: &mut SharedState) -> bool {
        let mut clicked = false;
        ui.with_layout(Layout::top_down_justified(Align::Min), |ui| {
            ui.add_space(4.0);
            ui.heading("hello_egui");
            ui.add_space(4.0);

            ui.label("Examples");
            ui.add_space(4.0);

            ui.spacing_mut().button_padding = egui::vec2(6.0, 4.0);

            for category in EXAMPLES {
                ui.small(category.name);
                for example in category.examples {
                    let route = format!("/example/{}", example.slug);
                    if ui
                        .selectable_label(
                            shared.active_route == route,
                            RichText::new(example.name).size(14.0),
                        )
                        .clicked()
                    {
                        clicked = true;
                        shared.tx.send(AppMessage::Navigate(route)).ok();
                    };
                }
            }
        });

        clicked
    }
}
