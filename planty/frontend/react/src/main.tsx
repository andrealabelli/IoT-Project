import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Link, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { API, request } from './api/client'

type Device = { device_id: string; name: string }

function Login() {
  const navigate = useNavigate()
  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    const data = await request('/auth/login', 'POST', { email: fd.get('email'), password: fd.get('password') })
    localStorage.setItem('token', data.access_token)
    navigate('/')
  }
  return <form onSubmit={onSubmit}><h2>Login</h2><input name='email' /><input name='password' type='password' /><button>Entra</button></form>
}

function Home() {
  const [devices, setDevices] = React.useState<Device[]>([])
  React.useEffect(() => { request('/devices').then(setDevices).catch(() => {}) }, [])
  return <div><h2>Devices</h2>{devices.map(d => <div key={d.device_id}><Link to={`/device/${d.device_id}`}>{d.name}</Link></div>)}</div>
}

function DevicePage() {
  const { id } = useParams()
  const [telemetry, setTelemetry] = React.useState<any>()
  const [ack, setAck] = React.useState<string>('')

  React.useEffect(() => {
    if (!id) return
    request(`/devices/${id}/latest`).then(setTelemetry).catch(() => {})
    const ws = new WebSocket(`${API.replace('http', 'ws')}/ws/${id}`)
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'ack') setAck(`${data.command} ${data.success ? 'OK' : 'ERR'} ${data.details || ''}`)
      if (data.type === 'telemetry') setTelemetry(data)
    }
    const ping = setInterval(() => ws.readyState === 1 && ws.send('keepalive'), 1000)
    return () => { clearInterval(ping); ws.close() }
  }, [id])

  return <div>
    <h3>Stato</h3>
    <p>{telemetry?.state || 'N/A'}</p>
    <h3>Telemetria</h3>
    <p>T: {telemetry?.air_temperature}°C</p>
    <p>RH: {telemetry?.air_humidity}%</p>
    <p>Soil: {telemetry?.soil_moisture}%</p>
    <h3>Comandi</h3>
    <button onClick={() => request(`/devices/${id}/irrigate`, 'POST', { duration_seconds: 5 })}>Irriga ora</button>
    <button onClick={() => request(`/devices/${id}/refresh`, 'POST')}>Aggiorna stato</button>
    <p>ACK: {ack || 'in attesa'}</p>
    <h3>Calibrazione</h3>
    <button onClick={() => request(`/devices/${id}/calibration`, 'POST', { soil_offset: 0, temp_offset: 0, humidity_offset: 0 })}>Reset offset</button>
  </div>
}

function App() {
  return <BrowserRouter><nav><Link to='/'>Home</Link> | <Link to='/login'>Login</Link></nav><Routes><Route path='/' element={<Home />} /><Route path='/login' element={<Login />} /><Route path='/device/:id' element={<DevicePage />} /></Routes></BrowserRouter>
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />)
