use eframe;
use eframe::{egui, Frame};
use egui::{Context, SidePanel, Ui, FontDefinitions, FontFamily};
use routes::router;
use std::num::NonZeroUsize;

mod futures;
mod routes;
mod shared_state;
mod sidebar;
mod example;
mod chat;

use hello_egui::inbox::UiInbox;
use hello_egui::router::EguiRouter;
use hello_egui::thumbhash;
use hello_egui_utils::center::Center;
use shared_state::SharedState;
use sidebar::SideBar;


pub enum AppMessage {
    Navigate(String),
}

// 폰트 설정 함수
fn configure_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();

    // 외부 폰트 데이터 추가
    fonts.font_data.insert(
        "NotoSansKR".to_owned(),
        egui::FontData::from_static(include_bytes!("../assets/fonts/NotoSansKR-Regular.ttf")),
    );

    // Proportional과 Monospace에 외부 폰트를 연결
    fonts.families.get_mut(&egui::FontFamily::Proportional).unwrap().insert(0, "NotoSansKR".to_owned());
    fonts.families.get_mut(&egui::FontFamily::Monospace).unwrap().insert(0, "NotoSansKR".to_owned());

    // 업데이트된 폰트를 egui에 적용
    ctx.set_fonts(fonts);
}

pub struct App {
    sidebar_expanded: bool,
    shared_state: SharedState,
    inbox: UiInbox<AppMessage>,
    router: EguiRouter<SharedState>,
}

impl App {
    pub fn new(ctx: &Context) -> Self {
        // 폰트 설정 호출
        configure_fonts(ctx);
        let (tx, inbox) = UiInbox::channel();
        let mut state = SharedState::new(tx);

        let router = router(&mut state);

        ctx.options_mut(|opts| {
            opts.max_passes = NonZeroUsize::new(4).unwrap();
        });

        Self {
            inbox,
            shared_state: state,
            sidebar_expanded: false,
            router,
        }
    }
}

impl eframe::App for App {
    fn update(&mut self, ctx: &Context, _frame: &mut Frame) {
        self.inbox.set_ctx(ctx);
        self.inbox.read_without_ctx().for_each(|msg| match msg {
            AppMessage::Navigate(route) => {
                self.router.navigate(&mut self.shared_state, route).unwrap();
            }
        });

        let width = ctx.screen_rect().width();
        let collapsible_sidebar = width < 800.0;
        let is_expanded = !collapsible_sidebar || self.sidebar_expanded;

        SidePanel::left("sidebar")
            .resizable(false)
            .exact_width(170.0)
            .show_animated(ctx, is_expanded, |ui| {
                if SideBar::ui(ui, &mut self.shared_state) {
                    self.sidebar_expanded = true;
                }
            });

        egui::CentralPanel::default()
            .frame(egui::Frame::none().fill(ctx.style().visuals.panel_fill.gamma_multiply(0.7)))
            .show(ctx, |ui| {
                if collapsible_sidebar {
                    ui.add_space(16.0);
                    ui.horizontal(|ui| {
                        ui.add_space(16.0);
                        if ui.add(egui::Button::new("☰")).clicked() {
                            self.sidebar_expanded = !self.sidebar_expanded;
                        }
                    });
                }

                if !(collapsible_sidebar && is_expanded) {
                    self.router.ui(ui, &mut self.shared_state);
                }
            });
    }
}

// // Helper function to create a demo area(center) with a title.
// pub fn demo_area(ui: &mut Ui, title: &'static str, width: f32, content: impl FnOnce(&mut Ui)) {
//     Center::new(title).ui(ui, |ui| {
//         let width = f32::min(ui.available_width() - 20.0, width);
//         ui.set_max_width(width);
//         ui.set_max_height(ui.available_height() - 20.0);

//         egui::Frame::none()
//             .fill(ui.style().visuals.panel_fill)
//             .rounding(10.0)
//             .inner_margin(20.0)
//             .show(ui, |ui| {
//                 ui.heading(title);
//                 ui.add_space(5.0);

//                 content(ui);
//             });
//     });
// }

pub fn demo_area(ui: &mut Ui, title: &'static str, width: f32, content: impl FnOnce(&mut Ui)) {
    let mut open = true; // Window의 열림/닫힘 상태를 추적
    
    egui::Window::new(title)
        .default_width(width)
        .resizable(true)
        .collapsible(true)
        .open(&mut open)
        .show(ui.ctx(), |ui| {
            content(ui);
        });
}

#[cfg(not(target_arch = "wasm32"))]
fn main() -> eframe::Result<()> {
    use eframe::NativeOptions;
    use egui::ViewportBuilder;

    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("Unable to create Runtime");

    // Enter the runtime so that `tokio::spawn` is available immediately.
    let _enter = rt.enter();

    // Execute the runtime in its own thread.
    // The future doesn't have to do anything. In this example, it just sleeps forever.
    std::thread::spawn(move || {
        rt.block_on(async {
            loop {
                tokio::time::sleep(std::time::Duration::from_secs(3600)).await;
            }
        });
    });

    let native_options = NativeOptions {
        viewport: ViewportBuilder::default()
            .with_inner_size([400.0, 400.0])
            .with_min_inner_size([400.0, 400.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Dnd Example App",
        native_options,
        Box::new(move |ctx| {
            egui_extras::install_image_loaders(&ctx.egui_ctx);
            Ok(Box::new(App::new(&ctx.egui_ctx)) as Box<dyn eframe::App>)
        }),
    )
}

// when compiling to web using trunk.
#[cfg(target_arch = "wasm32")]
fn main() {
    use wasm_bindgen::JsCast;
    let web_options = eframe::WebOptions::default();
    let element = eframe::web_sys::window()
        .expect("failed to get window")
        .document()
        .expect("failed to get document")
        .get_element_by_id("canvas")
        .expect("failed to get canvas element")
        .dyn_into::<eframe::web_sys::HtmlCanvasElement>()
        .unwrap();
    wasm_bindgen_futures::spawn_local(async {
        eframe::WebRunner::new()
            .start(
                element,
                web_options,
                Box::new(|ctx| {
                    egui_extras::install_image_loaders(&ctx.egui_ctx);
                    hello_egui::thumbhash::register(&ctx.egui_ctx);
                    Ok(Box::new(App::new(&ctx.egui_ctx)) as Box<dyn eframe::App>)
                }),
            )
            .await
            .expect("failed to start eframe");
    });
}
