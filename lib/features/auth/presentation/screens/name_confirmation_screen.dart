import 'package:flutter/material.dart';

import '../../data/profile_repository.dart';

class NameConfirmationScreen extends StatefulWidget {
  const NameConfirmationScreen({
    super.key,
    required this.profileRepository,
    required this.initialNombre,
    required this.initialApellido,
    required this.onConfirmed,
  });

  final ProfileRepository profileRepository;
  final String initialNombre;
  final String initialApellido;
  final Future<void> Function() onConfirmed;

  @override
  State<NameConfirmationScreen> createState() => _NameConfirmationScreenState();
}

class _NameConfirmationScreenState extends State<NameConfirmationScreen> {
  late final _nombreCtrl = TextEditingController(text: widget.initialNombre);
  late final _apellidoCtrl = TextEditingController(text: widget.initialApellido);
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _apellidoCtrl.dispose();
    super.dispose();
  }

  Future<void> _confirm() async {
    final nombre = _nombreCtrl.text.trim();
    final apellido = _apellidoCtrl.text.trim();
    if (nombre.isEmpty || apellido.isEmpty) {
      setState(() => _error = 'Nombre y apellido son obligatorios.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.profileRepository.confirmNombreApellido(nombre: nombre, apellido: apellido);
      await widget.onConfirmed();
    } catch (_) {
      if (mounted) setState(() => _error = 'No se pudo guardar. Verifica tu conexión e intenta de nuevo.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Confirma tus datos')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Verifica que tu nombre y apellido estén correctos antes de continuar.'),
              const SizedBox(height: 24),
              TextField(
                controller: _nombreCtrl,
                decoration: const InputDecoration(labelText: 'Nombre', border: OutlineInputBorder()),
                textCapitalization: TextCapitalization.words,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _apellidoCtrl,
                decoration: const InputDecoration(labelText: 'Apellido', border: OutlineInputBorder()),
                textCapitalization: TextCapitalization.words,
              ),
              if (_error != null) ...[
                const SizedBox(height: 16),
                Text(_error!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _saving ? null : _confirm,
                child: _saving
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Confirmar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
