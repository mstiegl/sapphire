""" Verify via the Method of Manufactured Solution (MMS) """
import firedrake as fe
import fempy.table
import math
import matplotlib.pyplot as plt
import pathlib


TIME_EPSILON = 1.e-8

def make_mms_verification_model_class(Model):

    class MMSVerificationModel(Model):
        
        def __init__(self, *args, **kwargs):
        
            super().__init__(*args, **kwargs)
            
            self._L2_error = None
            
        def init_solutions(self):
        
            self.init_manufactured_solution()
            
            super().init_solutions()
        
        def init_weak_form_residual(self):
        
            super().init_weak_form_residual()
            
            s = self.strong_form_residual(self.manufactured_solution)
            
            V = self.function_space
            
            if len(V) == 1:
            
                s = (s,)
            
            for psi, s_i in zip(fe.TestFunctions(V), s):
                
                self.weak_form_residual -= fe.inner(psi, s_i)
                
        def init_dirichlet_boundary_conditions(self):
            
            u_m = self.manufactured_solution
            
            W = self.function_space
            
            if len(W) == 1:
            
                u_m = (u_m,)
            
            self.dirichlet_boundary_conditions = [
                fe.DirichletBC(V, g, "on_boundary") 
                for V, g in zip(W, u_m)]
                
        def initial_values(self):
        
            initial_values = fe.Function(self.function_space)
            
            if (type(self.manufactured_solution) is not type([0,])) \
                    and (type(self.manufactured_solution) is not type((0,))):
            
                w_m = (self.manufactured_solution,)
                
            else:
            
                w_m = self.manufactured_solution
                    
            for u_m, V in zip(
                    w_m, self.function_space):
                
                initial_values.assign(fe.interpolate(u_m, V))
                
            return initial_values
            
        def L2_error(self):
            
            dx = self.integration_measure
            
            try:
            
                e = 0.
            
                for u_h, u_m in zip(
                        self.solution.split(), self.manufactured_solution):
                    
                    e += fe.assemble(fe.inner(u_h - u_m, u_h - u_m)*dx)

                e = math.sqrt(e)
                
            except NotImplementedError as error:
            
                u_h, u_m = self.solution, self.manufactured_solution
                
                e = math.sqrt(fe.assemble(fe.inner(u_h - u_m, u_h - u_m)*dx))
                
            return e
            
        def report(self, write_header = True):
            
            self._L2_error = self.L2_error()
            
            super().report(write_header = write_header)
            
    return MMSVerificationModel
    
    
def verify_spatial_order_of_accuracy(
        Model,
        expected_order,
        mesh_sizes,
        tolerance,
        constructor_kwargs = {},
        parameters = {},
        timestep_size = None,
        endtime = None,
        starttime = 0.,
        plot_errors = False,
        plot_solution = False,
        report = False):
    
    MMSVerificationModel = make_mms_verification_model_class(Model)
    
    table = fempy.table.Table(("h", "L2_error", "spatial_order"))
    
    print("")
    
    for meshsize in mesh_sizes:
        
        model = MMSVerificationModel(**constructor_kwargs, meshsize = meshsize)
        
        model.output_directory_path = model.output_directory_path.joinpath(
            "mms_space_p" + str(expected_order) + "/")
            
        if timestep_size is not None:
            
            model.output_directory_path = \
                model.output_directory_path.joinpath(
                "Deltat" + str(timestep_size))
        
        model.output_directory_path = model.output_directory_path.joinpath(
            "m" + str(meshsize) + "/")
        
        model.assign_parameters(parameters)
        
        if hasattr(model, "time"):
        
            model.time.assign(starttime)
            
            model.timestep_size.assign(timestep_size)
            
            model.run(endtime = endtime, plot = plot_solution, report = report)
        
        else:
        
            model.solve()
        
        table.append({
            "h": 1./float(model.meshsize),
            "L2_error": model.L2_error()})
            
        if len(table) > 1:
        
            h, e = table.data["h"], table.data["L2_error"]

            log = math.log
            
            r = h[-2]/h[-1]
            
            order = log(e[-2]/e[-1])/log(r)
            
            table.data["spatial_order"][-1] = order
        
        print(str(table))
    
    print("Last observed spatial order of accuracy is " + str(order))
    
    if plot_errors:
    
        h, e = table.data["h"], table.data["L2_error"]
        
        plt.loglog(h, e, marker = "o")
        
        plt.xlabel(r"$h$")
        
        plt.ylabel(r"$\Vert u - u_h \Vert$")
        
        plt.axis("equal")
        
        plt.grid(True)
        
        filepath = model.output_directory_path.joinpath(
            "e_vs_h").with_suffix(".png")
        
        print("Writing plot to " + str(filepath))
        
        plt.savefig(str(filepath))
        
        plt.close()
        
    assert(abs(order - expected_order) < tolerance)
    
    
def verify_temporal_order_of_accuracy(
        Model,
        expected_order,
        meshsize,
        timestep_sizes,
        endtime,
        tolerance,
        constructor_kwargs = {},
        parameters = {},
        starttime = 0.,
        plot_errors = False,
        plot_solution = False,
        report = False):
    
    MMSVerificationModel = make_mms_verification_model_class(Model)
    
    table = fempy.table.Table(("Delta_t", "L2_error", "temporal_order"))
    
    model = MMSVerificationModel(**constructor_kwargs, meshsize = meshsize)
    
    basepath = model.output_directory_path
    
    model.assign_parameters(parameters)
    
    print("")
    
    for timestep_size in timestep_sizes:
        
        model.timestep_size.assign(timestep_size)
        
        model.output_directory_path = basepath.joinpath(
            "mms_time_q" + str(expected_order) + "/")
        
        model.output_directory_path = model.output_directory_path.joinpath(
            "m" + str(meshsize))
            
        model.output_directory_path = model.output_directory_path.joinpath(
            "Deltat" + str(timestep_size))
        
        model.time.assign(starttime)
        
        model.update_initial_values()
        
        model.run(endtime = endtime, plot = plot_solution, report = report)
            
        table.append({
            "Delta_t": timestep_size,
            "L2_error": model.L2_error()})
            
        if len(table) > 1:
        
            Delta_t, e = table.data["Delta_t"], table.data["L2_error"]

            log = math.log
            
            r = Delta_t[-2]/Delta_t[-1]

            order = log(e[-2]/e[-1])/log(r)
    
            table.data["temporal_order"][-1] = order
        
        print(str(table))
        
    print("Last observed temporal order of accuracy is " + str(order))
    
    if plot_errors:
    
        Delta_t, e = table.data["Delta_t"], table.data["L2_error"]
        
        plt.loglog(Delta_t, e, marker = "o")
        
        plt.xlabel(r"$\Delta t$")
        
        plt.ylabel(r"$\Vert u - u_h \Vert$")
        
        plt.axis("equal")
        
        plt.grid(True)
        
        filepath = model.output_directory_path.joinpath(
            "e_vs_Delta_t").with_suffix(".png")
        
        print("Writing plot to " + str(filepath))
        
        plt.savefig(str(filepath))
        
        plt.close()
        
    assert(abs(order - expected_order) < tolerance)
    
    
def plot_manufactured_solution(
        Model,
        meshsize = 128,
        parameters = {},
        time = None):
        
    MMSVerificationModel = make_mms_verification_model_class(Model)
    
    model = MMSVerificationModel(meshsize = meshsize)

    model.init_manufactured_solution()
    
    if time is not None:
    
        model.time.assign(time)
    
    for u_m, V in zip(
            model.manufactured_solution, model.function_space):

        model.solution.assign(fe.interpolate(u_m, V))

    model.plot()

    