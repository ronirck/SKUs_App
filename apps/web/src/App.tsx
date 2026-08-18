import Encabezado from "@/components/Encabezado";
import ProductosTable from "@/components/ProductosTable";

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Encabezado />
      <main className="flex-1">
        <ProductosTable />
      </main>
      <footer className="border-t border-marca-borde bg-white">
        <div className="mx-auto w-full max-w-7xl px-6 py-5">
          <p className="versalita">Grupo Mayoreo · Panel interno</p>
        </div>
      </footer>
    </div>
  );
}
