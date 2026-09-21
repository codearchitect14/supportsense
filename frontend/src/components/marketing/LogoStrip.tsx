import { Container } from "../ui/Container";

const brands = ["Northpeak", "Vertex Retail", "Solstice Goods", "Marlow & Co.", "Fernbridge", "Astra Home"];

export function LogoStrip() {
  return (
    <section className="border-y border-slate-200 bg-white py-10">
      <Container>
        <p className="mb-7 text-center text-sm font-medium text-slate-500">
          Trusted by growing retail and e-commerce teams
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 opacity-70 grayscale">
          {brands.map((name) => (
            <span key={name} className="font-heading text-lg font-semibold text-slate-400">
              {name}
            </span>
          ))}
        </div>
      </Container>
    </section>
  );
}
