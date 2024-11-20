#![allow(clippy::needless_pass_by_value)]
use crate::example::EXAMPLES;
use crate::shared_state::SharedState;
use egui::Ui;
use egui_router::{EguiRouter, Request, Route, TransitionConfig};

pub fn example_route(req: Request<SharedState>) -> impl Route<SharedState> {
    let example_slug = req.params.get("slug").unwrap();

    let example = EXAMPLES
        .iter()
        .flat_map(|category| category.examples.iter())
        .find(|example| example.slug == example_slug)
        .unwrap();

    let mut example_ui = example.get();

    move |ui: &mut Ui, state: &mut SharedState| {
        example_ui.ui(ui, state);
    }
}

pub fn router(state: &mut SharedState) -> EguiRouter<SharedState> {
    EguiRouter::builder()
        .history({
            let default_path = "/hello_egui/#".to_string();
            #[cfg(target_arch = "wasm32")]
            let history = egui_router::history::BrowserHistory::new(default_path);
            #[cfg(not(target_arch = "wasm32"))]
            let history = egui_router::history::DefaultHistory::default();

            history
        })
        .transition(TransitionConfig::fade())
        .default_duration(0.3)
        .default_path("/")
        .route("/example/{slug}", example_route)
        .route_redirect("/", format!("/example/{}", EXAMPLES[0].examples[0].slug))
        .build(state)
}
