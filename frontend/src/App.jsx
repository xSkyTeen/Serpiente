import React, { useEffect, useState } from 'react';
import { ShieldAlert, Activity, Power, Lock } from 'lucide-react';

// --- MOCK DE SUPABASE PARA PREVISUALIZACIÓN ---
// NOTA: En tu proyecto local (VS Code), debes instalar: npm install @supabase/supabase-js
// y descomentar las líneas reales de importación y conexión.

// import { createClient } from '@supabase/supabase-js';
// const supabaseUrl = 'TU_URL_SUPABASE';
// const supabaseKey = 'TU_KEY_SUPABASE';
// const supabase = createClient(supabaseUrl, supabaseKey);

// --- SIMULACIÓN DE DATOS (Solo para que funcione en este editor) ---
const mockSupabase = {
  channel: (name) => ({
    on: (event, filter, callback) => {
      // Simulamos eventos en vivo
      const interval = setInterval(() => {
        if (name === 'machine_status') {
          // Simula cambio de estado aleatorio (Mantenimiento vs Producción)
          const isMaint = Math.random() > 0.8;
          callback({
            new: {
              estado_operativo: isMaint ? 'STOP' : 'RUN',
              modo_mantenimiento: isMaint
            }
          });
        } else if (name === 'actions') {
          // Simula alertas llegando
          if (Math.random() > 0.6) {
            const tipos = ['PARADA_TOTAL', 'ADVERTENCIA', 'LOG'];
            const motivos = ['Intrusión Crítica', 'Proximidad al borde', 'Acceso Técnico Autorizado'];
            const tipoIdx = Math.floor(Math.random() * tipos.length);

            callback({
              new: {
                id: Date.now(),
                accion: tipos[tipoIdx],
                motivo: motivos[tipoIdx],
                created_at: new Date().toISOString()
              }
            });
          }
        }
      }, 3000); // Cada 3 segundos manda un dato falso

      return {
        subscribe: () => {},
        unsubscribe: () => clearInterval(interval)
      };
    }
  }),
  removeChannel: () => {}
};

// Usamos el mock si no estamos en local
const supabase = mockSupabase;

function App() {
  const [systemState, setSystemState] = useState({ estado: 'RUN', mantenimiento: false });
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    // 1. Suscripción a cambios en Estado Maquina
    const channel1 = supabase
      .channel('machine_status')
      .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'estado_maquina' }, (payload) => {
        setSystemState({ estado: payload.new.estado_operativo, mantenimiento: payload.new.modo_mantenimiento });
      });
      // .subscribe(); // En mock no es necesario, pero en real sí

    // 2. Suscripción a Acciones (Alertas)
    const channel2 = supabase
      .channel('actions')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'acciones_sistema' }, (payload) => {
        setAlerts((prev) => [payload.new, ...prev].slice(0, 5)); // Guardar ultimas 5
      });
      // .subscribe();

    return () => {
      // Limpieza (En real)
      // supabase.removeChannel(channel1);
      // supabase.removeChannel(channel2);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8 font-mono">
      <header className="mb-8 border-b border-slate-700 pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400">S.E.R.P.I.E.N.T.E. SCADA</h1>
          <p className="text-slate-400 text-sm">Industrial Safety Monitoring System</p>
        </div>
        <div className={`px-4 py-2 rounded-lg font-bold transition-colors duration-500 ${systemState.mantenimiento ? 'bg-yellow-600' : 'bg-green-600'}`}>
          {systemState.mantenimiento ? '🛠️ MODO MANTENIMIENTO' : '🟢 PRODUCCIÓN NORMAL'}
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* PANEL DE ESTADO */}
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="text-cyan-400" />
            <h2 className="text-xl font-bold">Estado Máquina</h2>
          </div>
          <div className={`text-center py-8 rounded-lg border-2 transition-all duration-500 ${
            systemState.estado === 'RUN' ? 'border-green-500 bg-green-900/20 text-green-400' : 'border-red-500 bg-red-900/20 text-red-500 animate-pulse'
          }`}>
            <Power size={48} className="mx-auto mb-2" />
            <span className="text-2xl font-black tracking-widest">{systemState.estado}</span>
          </div>
        </div>

        {/* LOG DE ALERTAS */}
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <ShieldAlert className="text-orange-400" />
            <h2 className="text-xl font-bold">Registro de Eventos (STRIPS)</h2>
          </div>
          <div className="space-y-2">
            {alerts.length === 0 && <p className="text-slate-500 italic">Esperando eventos del sistema...</p>}
            {alerts.map((alert) => (
              <div key={alert.id} className={`p-3 rounded border-l-4 flex justify-between items-center transition-all duration-300 ${
                alert.accion === 'PARADA_TOTAL' ? 'bg-red-900/30 border-red-500' : 
                alert.accion === 'ADVERTENCIA' ? 'bg-yellow-900/30 border-yellow-500' : 'bg-slate-700 border-blue-500'
              }`}>
                <div>
                  <span className="font-bold block">{alert.accion}</span>
                  <span className="text-sm text-slate-300">{alert.motivo}</span>
                </div>
                <span className="text-xs text-slate-500">{new Date(alert.created_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;