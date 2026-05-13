import reflex as rx

from harun_site.theme import BORDER, PRIMARY, TEXT_MUTED, FONT_MONO


def footer() -> rx.Component:
	return rx.box(
		rx.hstack(
			rx.text(
				"© 2025 harun dülger",
				font_family=FONT_MONO,
				font_size="0.75em",
				color=TEXT_MUTED,
			),
			rx.hstack(
				rx.link(
					"github",
					href="https://github.com/harundulger",
					font_family=FONT_MONO,
					font_size="0.78em",
					color=TEXT_MUTED,
					_hover={"color": PRIMARY},
					text_decoration="none",
				),
				rx.link(
					"linkedin",
					href="https://linkedin.com/in/harundulger",
					font_family=FONT_MONO,
					font_size="0.78em",
					color=TEXT_MUTED,
					_hover={"color": PRIMARY},
					text_decoration="none",
				),
				rx.link(
					"mail",
					href="mailto:harun@ornek.com",
					font_family=FONT_MONO,
					font_size="0.78em",
					color=TEXT_MUTED,
					_hover={"color": PRIMARY},
					text_decoration="none",
				),
				style={"gap": "1.5em"},
			),
			justify="between",
			align="center",
			style={"max_width": "1100px", "margin": "0 auto", "width": "100%"},
			width="100%",
		),
		background="transparent",
		border_top=f"1px solid {BORDER}",
		padding="1.5em 3em",
		width="100%",
	)